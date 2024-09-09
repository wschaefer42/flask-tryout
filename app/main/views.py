import json
from flask import render_template, request, current_app, Response, make_response, redirect, url_for
from flask_login import login_required, current_user
from . import main
from .. import db, trace
from ..decorators import admin_required, permission_required
from ..models import Post, User, Permission, Comment
from ..types import PostFilter
from ..utils import str2bool


@main.route('/', )
@main.route('/index')
@login_required
def index():
    post_filter = PostFilter.ALL
    if current_user.is_authenticated:
        post_filter = PostFilter.by_value(request.cookies.get('show_followed', post_filter), PostFilter.ALL)
    current_app.logger.debug('post_filter: %s', post_filter)
    if post_filter == PostFilter.FOLLOWED:
        query = current_user.followed_posts
    elif post_filter == PostFilter.MYSELF:
        query = current_user.myself_posts
    else:
        query = Post.query
    posts = query.order_by(Post.timestamp.desc())
    return render_template('index.html', show_followed=post_filter.value, posts=posts)


@main.route('/admin')
@login_required
@admin_required
def for_admin_only():
    return "For Admin Only"

@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def for_moderators_only():
    comments = Comment.query.order_by(Comment.timestamp.desc())
    return render_template('moderate.html', comments=comments)

@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_disable(id):
    status = request.args.get('status', default=True, type=str2bool)
    trace.info(f'Disable comment id={id} status={status}')
    comment = Comment.query.get_or_404(id)
    comment.disabled = status
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.for_moderators_only'))

@main.route('/post/<username>', methods=['GET', 'POST'])
@login_required
def send_post(username):
    try:
        user = username and User.query.filter_by(username=username).first() or current_user
        if request.method == 'POST':
            body = request.args.get('body') or "Hello World"
            post = Post.query.filter_by(author=user).filter_by(body=body).first()
            if not post:
                current_app.logger.info(f'Post {body} from {user}')
                post = Post(body=body, author=user)
                db.session.add(post)
                db.session.commit()
                return Response("Post was added", 201)
            else:
                return Response("Post already exists", 204)
        elif request.method == 'GET':
            posts = []
            for post in Post.query.filter_by(author=user).all():
                posts.append(post.body)
            return json.dumps(posts)
    except Exception as e:
        return Response(str(e), 500)


@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)

@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)  # 30 days
    return resp

@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)  # 30 days
    return resp

@main.route('/show/<tab>')
@login_required
def show_posts(tab):
    resp = make_response(redirect(url_for('.index')))
    post_filter = PostFilter.by_value(tab)
    if post_filter is None:
        raise Exception('Invalid tab {}'.format(tab))
    resp.set_cookie('show_followed', post_filter.value, max_age=30*24*60*60)  # 30 days
    return resp

