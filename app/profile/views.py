from flask import abort, render_template, flash, url_for, redirect
from flask_login import login_required, current_user, login_user

from . import profile
from ..decorators import permission_required
from ..models import User, Post, Permission

@profile.route('/')
def list_profiles():
    return render_template('profile/list_profiles.html', users=User.query.all())

@profile.route('/<username>')
def show_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.timestamp.desc()).all()
    return render_template('profile/show_profile.html', user=user, posts=posts)

@profile.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    pass

@profile.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_profile_admin(id):
    pass

@profile.route('/switch-to/<username>')
@login_required
def switch_to(username):
    user = User.query.filter_by(username=username).first_or_404()
    login_user(user)
    flash('You are now logged in as {}'.format(username))
    return redirect(url_for('.show_profile', username=username))

@profile.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if current_user.is_following(user):
        flash('You are already following {}'.format(username))
        return redirect(url_for('main.index'))
    current_user.follow(user)
    flash('You are now following {}'.format(username))
    return redirect(url_for('.show_profile', username=current_user.username))

@profile.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    pass

@profile.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    follower_list = [{'user': item.follower, 'timestamp': item.timestamp} for item in user.followers.all()]
    return render_template('profile/followers.html', title="Followers of", user=user, followers=follower_list)

@profile.route('/followed_by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first_or_404()
    follower_list = [{'user': item.followed, 'timestamp': item.timestamp} for item in user.followed.all()]
    return render_template('profile/followers.html', title="Following by", user=user, followers=follower_list)

