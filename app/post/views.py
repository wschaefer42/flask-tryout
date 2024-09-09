from flask import redirect, url_for, flash, render_template, request, current_app
from flask_login import current_user
from sqlalchemy import func
from . import post
from .forms import PostForm, CommentForm
from .. import db
from ..models import Permission, Post, Comment
from ..utils import sanitize_html, sanitize_text


@post.route('/', methods=['GET', 'POST'])
def show_posts():
    form = PostForm()
    if request.method == 'POST':
        if form.submit.data:
            current_app.logger.debug("New post")
            if current_user.can(Permission.WRITE) and form.validate_on_submit():
                if not Post.query.filter(func.lower(Post.body) == func.lower(form.body.data)).first():
                    new_post = Post(body=form.body.data, author=current_user)
                    db.session.add(new_post)
                    db.session.commit()
                    return redirect(url_for('.show_posts'))
                else:
                    flash('Such a post already exists!', 'warning')
        elif form.apply.data:
            form.body.data = sanitize_html(form.body.data)
    posts = (Post.query.filter_by(author=current_user).order_by(Post.timestamp.desc()).all())
    return render_template('post/show_posts.html', form=form, posts=posts)

@post.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    form = PostForm(obj=post)
    current_app.logger.info(f"Post type is {form.body_type.data}")
    if request.method == 'POST':
        if form.submit.data:
            if form.validate_on_submit():
                form.populate_obj(post)
                if post.body_type == Post.BodyType.HTML:
                    post.body = sanitize_html(form.body.data)
                elif post.body_type == Post.BodyType.TEXT:
                    post.body = sanitize_text(form.body.data)
            db.session.add(post)
            db.session.commit()
            flash("Post updated.", "success")
        elif form.apply.data:
            form.body.data = sanitize_html(form.body.data)
    return render_template('post/edit_post.html', form=form)

@post.route('/show/<int:post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been published.')
        return redirect(url_for('post.show_post', post_id=post.id, page=-1))
    comments = post.comments.order_by(Comment.timestamp.asc())
    return render_template('post/single_post.html', posts=[post], form=form, comments=comments)
