from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .decorators import (
    editor_required,
    journalist_required,
    login_required_custom,
    reader_required,
)
from .forms import ArticleForm, NewsletterForm, PublisherForm
from .models import Article, Newsletter, Publisher

User = get_user_model()


# ---------------------------------------------------------------------------
# Article views
# ---------------------------------------------------------------------------

def article_list(request):
    """
    Display a paginated list of all approved articles, newest first.

    Accessible to all users (authenticated and anonymous).
    """
    qs = (
        Article.objects
        .filter(approved=True)
        .select_related('author', 'publisher')
        .order_by('-created_at')
    )
    paginator = Paginator(qs, 9)
    page_obj  = paginator.get_page(request.GET.get('page'))
    return render(request, 'news/article_list.html', {'page_obj': page_obj})


def article_detail(request, pk):
    """
    Display a single article.

    Unapproved articles are visible only to the article's author and editors.
    All other users receive a 403 response for unapproved articles.
    """
    article = get_object_or_404(Article, pk=pk)
    if not article.approved:
        user = request.user
        is_author = user.is_authenticated and article.author == user
        is_editor = user.is_authenticated and user.is_editor()
        if not (is_author or is_editor):
            return render(request, '403.html', status=403)

    subscribed_journalist = (
        request.user.is_authenticated
        and request.user.is_reader()
        and request.user.subscribed_journalists.filter(
            pk=article.author.pk,
        ).exists()
    )
    subscribed_publisher = (
        request.user.is_authenticated
        and request.user.is_reader()
        and article.publisher is not None
        and request.user.subscribed_publishers.filter(
            pk=article.publisher.pk,
        ).exists()
    )
    return render(request, 'news/article_detail.html', {
        'article':               article,
        'subscribed_journalist': subscribed_journalist,
        'subscribed_publisher':  subscribed_publisher,
    })


@journalist_required
def create_article(request):
    """
    Allow a journalist to create a new draft article or submit one for review.

    Two submit buttons drive the behaviour:
    - ``Save Draft``           – saves with submitted=False
    - ``Submit for Review`` – saves submitted=True, queues for editor
    """
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article          = form.save(commit=False)
            article.author   = request.user
            article.submitted = request.POST.get('action') == 'submit'
            article.save()
            if article.submitted:
                messages.success(
                    request,
                    f'"{article.title}" submitted for editorial review.',
                )
            else:
                messages.success(request, f'"{article.title}" saved as draft.')
            return redirect('news:journalist_dashboard')
    else:
        form = ArticleForm()
    return render(
        request,
        'news/article_form.html',
        {'form': form, 'editing': False},
    )


@login_required_custom
def edit_article(request, pk):
    """
    Allow the article's author or any editor to edit an article.

    A journalist who did not author the article receives a 403 response.
    """
    article = get_object_or_404(Article, pk=pk)
    user    = request.user
    if not (
        user.is_editor()
        or (user.is_journalist() and article.author == user)
    ):
        return render(request, '403.html', status=403)
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            updated = form.save(commit=False)
            if not article.approved:
                # Only allow journalists to change submission state
                # on unapproved articles
                if user.is_journalist():
                    updated.submitted = request.POST.get('action') == 'submit'
            updated.save()
            if not article.approved and user.is_journalist():
                if updated.submitted:
                    messages.success(
                        request,
                        f'"{updated.title}" submitted for review.',
                    )
                else:
                    messages.success(
                        request,
                        f'"{updated.title}" saved as draft.',
                    )
            else:
                messages.success(
                    request, f'"{updated.title}" updated.',
                )
            return redirect('news:article_detail', pk=article.pk)
    else:
        form = ArticleForm(instance=article)
    return render(
        request,
        'news/article_form.html',
        {'form': form, 'editing': True, 'article': article},
    )


@login_required_custom
def delete_article(request, pk):
    """
    Allow the article's author or any editor to delete an article.

    Displays a confirmation page on GET and performs the deletion on POST.
    """
    article = get_object_or_404(Article, pk=pk)
    user    = request.user
    if not (
        user.is_editor()
        or (user.is_journalist() and article.author == user)
    ):
        return render(request, '403.html', status=403)
    if request.method == 'POST':
        title = article.title
        article.delete()
        messages.success(request, f'"{title}" deleted.')
        return redirect(
            'news:editor_queue'
            if user.is_editor()
            else 'news:journalist_dashboard'
        )
    cancel_url = reverse('news:article_detail', args=[pk])
    return render(
        request,
        'news/confirm_delete.html',
        {
            'object': article,
            'object_type': 'article',
            'cancel_url': cancel_url,
        },
    )


# ---------------------------------------------------------------------------
# Editor views
# ---------------------------------------------------------------------------

@editor_required
def editor_queue(request):
    """
    Display all unapproved articles that have been submitted for review,
    ordered by submission date (oldest first).

    Accessible only to editors.
    """
    articles = (
        Article.objects
        .filter(approved=False, submitted=True)
        .select_related('author', 'publisher')
        .order_by('created_at')
    )
    return render(request, 'news/article_approve.html', {'articles': articles})


@editor_required
def approve_article(request, pk):
    """
    Approve a pending article.

    Sets the private _just_approved flag on the instance before saving so
    the post_save signal (Phase 4) can distinguish a new approval from an
    ordinary re-save and avoid sending duplicate emails or tweets.
    """
    article = get_object_or_404(Article, pk=pk)
    if request.method == 'POST':
        if not article.approved:
            article._just_approved = True
            article.approved = True
            article.save()
            messages.success(
                request,
                f'"{article.title}" approved and published.',
            )
        else:
            messages.info(request, f'"{article.title}" was already approved.')
    return redirect('news:editor_queue')


@editor_required
def reject_article(request, pk):
    """
    Return a pending article to the journalist without approving it.

    The article remains in the queue (approved=False); a flash message
    notifies the editor that the article was returned.
    """
    article = get_object_or_404(Article, pk=pk)
    if request.method == 'POST':
        messages.warning(
            request,
            f'"{article.title}" returned to '
            f'{article.author.username} without approval.',
        )
    return redirect('news:editor_queue')


# ---------------------------------------------------------------------------
# Journalist dashboard
# ---------------------------------------------------------------------------

@journalist_required
def journalist_dashboard(request):
    """
    Show the logged-in journalist their own articles and newsletters.

    Articles are grouped by approval status so the journalist can see
    which drafts are pending review.
    """
    articles    = Article.objects.filter(
        author=request.user,
    ).order_by('-created_at')
    newsletters = Newsletter.objects.filter(
        author=request.user,
    ).order_by('-created_at')
    return render(
        request,
        'news/journalist_dashboard.html',
        {'articles': articles, 'newsletters': newsletters},
    )


# ---------------------------------------------------------------------------
# Newsletter views
# ---------------------------------------------------------------------------

def newsletter_list(request):
    """
    Display a list of all newsletters, newest first.

    Accessible to all users.
    """
    newsletters = (
        Newsletter.objects
        .select_related('author')
        .order_by('-created_at')
    )
    return render(
        request,
        'news/newsletter_list.html',
        {'newsletters': newsletters},
    )


def newsletter_detail(request, pk):
    """
    Display a single newsletter with its included articles.

    Accessible to all users.
    """
    newsletter = get_object_or_404(
        Newsletter.objects.prefetch_related('articles__author'), pk=pk
    )
    return render(
        request,
        'news/newsletter_detail.html',
        {'newsletter': newsletter},
    )


@journalist_required
def create_newsletter(request):
    """
    Allow a journalist to create a new newsletter.

    The logged-in user is set as the author before saving.
    """
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.save()
            form.save_m2m()
            messages.success(
                request,
                f'Newsletter "{newsletter.title}" created.',
            )
            return redirect('news:journalist_dashboard')
    else:
        form = NewsletterForm()
    return render(
        request,
        'news/newsletter_form.html',
        {'form': form, 'editing': False},
    )


@login_required_custom
def edit_newsletter(request, pk):
    """
    Allow the newsletter's author or any editor to edit a newsletter.

    A journalist who did not author the newsletter receives a 403 response.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)
    user       = request.user
    if not (
        user.is_editor()
        or (user.is_journalist() and newsletter.author == user)
    ):
        return render(request, '403.html', status=403)
    if request.method == 'POST':
        form = NewsletterForm(request.POST, instance=newsletter)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Newsletter "{newsletter.title}" updated.',
            )
            return redirect('news:newsletter_detail', pk=newsletter.pk)
    else:
        form = NewsletterForm(instance=newsletter)
    return render(
        request,
        'news/newsletter_form.html',
        {'form': form, 'editing': True, 'newsletter': newsletter},
    )


@login_required_custom
def delete_newsletter(request, pk):
    """
    Allow the newsletter's author or any editor to delete a newsletter.

    Displays a confirmation page on GET and performs the deletion on POST.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)
    user       = request.user
    if not (
        user.is_editor()
        or (user.is_journalist() and newsletter.author == user)
    ):
        return render(request, '403.html', status=403)
    if request.method == 'POST':
        title = newsletter.title
        newsletter.delete()
        messages.success(request, f'Newsletter "{title}" deleted.')
        return redirect(
            'news:newsletter_list'
            if user.is_editor()
            else 'news:journalist_dashboard'
        )
    cancel_url = reverse('news:newsletter_detail', args=[pk])
    return render(
        request,
        'news/confirm_delete.html',
        {
            'object': newsletter,
            'object_type': 'newsletter',
            'cancel_url': cancel_url,
        },
    )


# ---------------------------------------------------------------------------
# Publisher & journalist profile views
# ---------------------------------------------------------------------------

@editor_required
def create_publisher(request):
    """
    Allow an editor to create a new publisher from the web interface.

    On GET  — render a blank PublisherForm.
    On POST — validate and save; redirect to the new publisher's detail page.
    """
    form = PublisherForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        publisher = form.save()
        messages.success(request, f'Publisher "{publisher.name}" created.')
        return redirect('news:publisher_detail', pk=publisher.pk)
    return render(
        request,
        'news/publisher_form.html',
        {'form': form, 'editing': False},
    )


@editor_required
def edit_publisher(request, pk):
    publisher = get_object_or_404(Publisher, pk=pk)
    form = PublisherForm(
        request.POST or None,
        request.FILES or None,
        instance=publisher,
    )
    if form.is_valid():
        form.save()
        messages.success(
            request, f'Publisher "{publisher.name}" updated.',
        )
        return redirect('news:publisher_detail', pk=publisher.pk)
    return render(
        request,
        'news/publisher_form.html',
        {'form': form, 'editing': True, 'publisher': publisher},
    )


@editor_required
def delete_publisher(request, pk):
    publisher = get_object_or_404(Publisher, pk=pk)
    if request.method == 'POST':
        name = publisher.name
        publisher.delete()
        messages.success(request, f'Publisher "{name}" deleted.')
        return redirect('news:article_list')
    cancel_url = reverse('news:publisher_detail', args=[pk])
    return render(
        request,
        'news/confirm_delete.html',
        {
            'object': publisher,
            'object_type': 'publisher',
            'cancel_url': cancel_url,
        },
    )


def publisher_detail(request, pk):
    """
    Display a publisher's profile page and their latest approved articles.

    Readers see a Subscribe / Unsubscribe toggle button.
    """
    publisher = get_object_or_404(Publisher, pk=pk)
    articles  = (
        publisher.articles
        .filter(approved=True)
        .select_related('author')
        .order_by('-created_at')
    )
    subscribed = (
        request.user.is_authenticated
        and request.user.is_reader()
        and request.user.subscribed_publishers.filter(
            pk=publisher.pk,
        ).exists()
    )
    return render(
        request,
        'news/publisher_detail.html',
        {
            'publisher':  publisher,
            'articles':   articles,
            'subscribed': subscribed,
        },
    )


def journalist_profile(request, pk):
    """
    Display a journalist's profile page and their approved articles.

    Readers see a Subscribe / Unsubscribe toggle button.
    """
    journalist = get_object_or_404(User, pk=pk, role='journalist')
    articles   = (
        journalist.articles
        .filter(approved=True)
        .select_related('publisher')
        .order_by('-created_at')
    )
    subscribed = (
        request.user.is_authenticated
        and request.user.is_reader()
        and request.user.subscribed_journalists.filter(
            pk=journalist.pk,
        ).exists()
    )
    return render(
        request,
        'news/journalist_profile.html',
        {
            'journalist': journalist,
            'articles':   articles,
            'subscribed': subscribed,
        },
    )


# ---------------------------------------------------------------------------
# Subscription views
# ---------------------------------------------------------------------------

@reader_required
def subscribe_publisher(request, pk):
    """
    Toggle the current reader's subscription to a publisher.

    On POST, adds or removes the publisher from the reader's
    subscribed_publishers field and shows a flash message.  Redirects back
    to the publisher's profile page.
    """
    publisher = get_object_or_404(Publisher, pk=pk)
    if request.method == 'POST':
        if request.user.subscribed_publishers.filter(pk=publisher.pk).exists():
            request.user.subscribed_publishers.remove(publisher)
            messages.info(
                request, f'Unsubscribed from {publisher.name}.',
            )
        else:
            request.user.subscribed_publishers.add(publisher)
            messages.success(
                request, f'Subscribed to {publisher.name}.',
            )
    return redirect('news:publisher_detail', pk=pk)


@reader_required
def subscribe_journalist(request, pk):
    """
    Toggle the current reader's subscription to a journalist.

    On POST, adds or removes the journalist from the reader's
    subscribed_journalists field and shows a flash message.  Redirects back
    to the journalist's profile page.
    """
    journalist = get_object_or_404(User, pk=pk, role='journalist')
    if request.method == 'POST':
        name = journalist.get_full_name() or journalist.username
        if request.user.subscribed_journalists.filter(
            pk=journalist.pk,
        ).exists():
            request.user.subscribed_journalists.remove(journalist)
            messages.info(
                request, f'Unsubscribed from {name}.',
            )
        else:
            request.user.subscribed_journalists.add(journalist)
            messages.success(
                request, f'Subscribed to {name}.',
            )
    return redirect('news:journalist_profile', pk=pk)
