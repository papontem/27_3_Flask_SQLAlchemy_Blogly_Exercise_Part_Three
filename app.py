"""Blogly application."""

from flask import Flask, request, render_template, redirect, flash, session, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Post, Tag, PostTag
from secrets import RENDER_ENV_VAR

app = Flask(__name__)

# Flask-SQLAlchemy settings
# #### Local db
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///blogly'

# #### Local ElephantSQL connection works 
# app.config['SQLALCHEMY_DATABASE_URI'] = RENDER_ENV_VAR['ELEPHANT_DATABASE_URL'] 

#### Live render works now with addition of secrets file.
app.config['SQLALCHEMY_DATABASE_URI'] = RENDER_ENV_VAR['DATABASE_URL'] 

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

# Flask-Debugtoolbar settings
app.config['SECRET_KEY'] = "oh-so-secret"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
debug = DebugToolbarExtension(app) 

# FSQLA Init
connect_db(app)
db.create_all()

#ROUTES
@app.route('/') 
def homepage(): 
    """ Redirect to list of users. (We'll fix this in a later step). """
    # return render_template("home.html")
    return redirect('/users')

@app.route('/users')
def list_user():
    """ a lists of all posts titles
        Show all users.
        Make these links to view the detail page for the user.
        Have a link here to the add-user form.
    """
    users = User.query.all()
    return render_template("users.html", users = users)

@app.route('/users/new')
def new_user():
    """ Show an add form for users"""
    return render_template("new_user_form.html")

@app.route('/users/new', methods=["POST"]) 
def post_user():
    """ Process the add form, adding a newly created user and going back to /users"""
    first_name = request.form["first_name"]
    last_name = request.form.get("last_name")
    img_url = request.form.get("img_url")
    # create user model instance
    new_user = User(first_name=first_name, last_name=last_name,img_url=img_url)
    # commit the new user to the psql database thanx to SQLALCHEMY
    
    db.session.add(new_user)
    db.session.commit()

    return redirect('/users')

@app.route('/users/<int:user_id>')
def detail_user(user_id):
    """ 
        Show information about the given user.
        Have a button to get to their edit page,
          and a button to delete the user.
    """

    user = User.query.get_or_404(user_id)
    return render_template("details_user.html", user=user)

@app.route('/users/<int:user_id>/edit')
def show_user_edit_page(user_id):
    """
        Show the edit page for a user.
        Have a cancel button that returns to the detail page for a user,
          and a save button that updates the user.
    """

    user = User.query.get_or_404(user_id)
    return render_template("edit_user.html", user=user)

@app.route('/users/<int:user_id>/edit', methods=["POST"])
def edit_the_user(user_id):
    """Process the edit form, returning the user to the /users page."""

    user = User.query.get_or_404(user_id)

    edit_first_name = request.form["first_name"]
    edit_last_name = request.form["last_name"]
    edit_img_url = request.form["img_url"]
    

    user.first_name = edit_first_name
    user.last_name = edit_last_name
    user.img_url = edit_img_url
    
    db.session.add(user)
    db.session.commit()

    return redirect("/users")

@app.route('/users/<int:user_id>/delete', methods=["POST"])
def delete_the_user(user_id):
    """Delete The User"""
    db.session.delete(User.query.get_or_404(user_id))
    db.session.commit()
    return redirect("/users")


# GET /users/<int:user_id>/posts/new
@app.route('/users/<int:user_id>/posts/new')
def new_post(user_id):
    """ Show form to add a post for that user. """
    
    user = User.query.get_or_404(user_id)
    
    tags_list = Tag.query.all()

    return render_template('new_post_form.html', user=user, tags_list=tags_list)

# POST /users/<int:user_id>/posts/new
@app.route('/users/<int:user_id>/posts/new',methods=["POST"])
def new_post_form_submitted(user_id):
    """ 
        Process the add post form; add post to posts table with-
        -user_id and redirect to the user detail page. 
    """
   
    user = User.query.get_or_404(user_id)
   
    title = request.form["title"]
    content = request.form["content"]
    new_post = Post.create_post(user, title, content)
    
    tags_id_list = request.form.getlist('tags_id_list')
    # tags_id_list is an integer array. ex: [1,2,6,20]
    for tag_id in tags_id_list:
        # from our post go to its has_tags array and add the tag we find by querying the Tag model.
        new_post.has_tags.append(Tag.query.get_or_404(tag_id))

    db.session.add(new_post)
    db.session.commit()
    
    return redirect(f'/users/{user.id}')

# GET /posts 
@app.route('/posts')
def list_posts():
    """ 
        Show posts
        Show only their titles within an anchor tag , and their author within an anchor tag
        Make these links to view the detail page for the post, and for the user
    """
    posts = Post.query.all()

    return render_template("posts.html", posts=posts)


# # GET /posts/<int:post_id>
@app.route('/posts/<int:post_id>')
def details_post(post_id):
    """
        Show a post details page.
        title, content, author, time of posting
        Show buttons to edit and delete the post.
    """
    post = Post.query.get_or_404(post_id)

    return render_template('details_post.html', post=post)

# # GET /posts/<int:post_id>/edit
@app.route('/posts/<int:post_id>/edit')
def show_edit_post_form(post_id):
    """ Show form to edit a post, and to cancel (back to user page). """
    
    post = Post.query.get_or_404(post_id)

    tags_list = Tag.query.all()

    return render_template('edit_post.html', post=post, tags_list=tags_list )

# # POST /posts/<int:post_id>/edit
@app.route('/posts/<int:post_id>/edit', methods=["POST"])
def edit_post_form_submitted(post_id):
    """ Handle editing of a post. Redirect back to the post view. """
    post = Post.query.get_or_404(post_id)
    
    editing_title = request.form["title"]
    editing_content = request.form["content"]
    
    post.title = editing_title
    post.content = editing_content

    # ## TODO CHANGE POST TAGS delete post tag relations no longer needed
    old_tags_id_list = [tag.id for tag in post.has_tags] # has tags we may want to keep, some we may want to remove
    
    edited_tags_id_list = request.form.getlist('tags_id_list') # has what tags the post should now have

    # remove tags relation, the ones we want to remove that are in old list but not in the edited list
    for tag_id in old_tags_id_list:
        if tag_id not in edited_tags_id_list:
            post.has_tags.remove(Tag.query.get_or_404(tag_id))

    # add tags relation
    for tag_id in edited_tags_id_list:
        if tag_id not in old_tags_id_list:
            # from our post go to its has_tags array and add the tag we find it didnt have.
            post.has_tags.append(Tag.query.get_or_404(tag_id))


    db.session.add(post)
    db.session.commit()

    return redirect(f"/posts/{post.id}")

# # POST /posts/<int:post_id>/delete
@app.route('/posts/<int:post_id>/delete', methods=["POST"])
def delete_post(post_id):
    """Delete the post. redirect to user details page"""

    # # Pythons Native Debugger here to help ^_^ !! 
    # import pdb
    # pdb.set_trace()

    post = Post.query.get_or_404(post_id)
    #save author id int for redirecting after deletion
    post_author_id = post.author_user.id

    all_tags_of_this_post = post.has_tags
   
    for tag in all_tags_of_this_post:

        tag.has_posts.remove(post)
        # PAM: i added and commit a post to session here to resolve this Error:
        
        # sqlalchemy.orm.exc.StaleDataError: DELETE statement on table 'posts_tags' expected to delete 2 row(s); Only 1 were matched.

        # PAM: seems if i delete a tag its ok it it doesnt have any posts , 
        # but if i delete multiple ralations between them in post_tags before 
        # commiting to session, only the first has an effect and the rest dont get treated the same way?
        
        db.session.add(tag)
        db.session.commit()


    db.session.delete(post)
    db.session.commit()

    return redirect(f'/users/{post_author_id}')

# GET /tags
@app.route('/tags')
def list_tags():
    """
        Lists all tags, with links to the tag detail page.
    """
    tags = Tag.query.all()

    return render_template("tags.html", tags=tags)


# GET /tags/[tag-id]
@app.route('/tags/<int:tag_id>')
def details_tag(tag_id):
    """
        Show detail about a tag. Have links to edit form and to delete.
    """
    tag = Tag.query.get_or_404(tag_id)

    return render_template("details_tag.html", tag=tag)

# GET /tags/new
@app.route('/tags/new')
def new_tag_form():
    """
        Shows a form to add a new tag.
    """

    return render_template("new_tag_form.html")

# POST /tags/new
@app.route('/tags/new', methods=["POST"])
def new_tag_form_submitted():
    """
        Process add form, adds tag, and redirect to tag list.
    """
    
    new_tag_name = request.form.get("name")

    new_tag = Tag(name = new_tag_name)

    db.session.add(new_tag)
    db.session.commit()

    return redirect("/tags")

# GET /tags/[tag-id]/edit
@app.route('/tags/<int:tag_id>/edit')
def edit_tag_form(tag_id):
    """
        Show edit form for a tag.
    """
    tag = Tag.query.get_or_404(tag_id)
    return render_template("edit_tag.html", tag=tag)

# POST /tags/[tag-id]/edit
@app.route('/tags/<int:tag_id>/edit', methods=["POST"])
def edit_tag_form_submitted(tag_id):
    """
        Process edit form, edit tag, and redirects to the tags list.
    """
    new_name = request.form.get("name")
    
    tag = Tag.query.get_or_404(tag_id)

    tag.name = new_name
    
    db.session.add(tag)
    db.session.commit()

    return redirect("/tags")

# POST /tags/[tag-id]/delete
@app.route('/tags/<int:tag_id>/delete', methods=["POST"])
def delete_tag(tag_id):
    """
        Delete a tag.
    """

    tag = Tag.query.get_or_404(tag_id)
   
    all_posts_with_tag = tag.has_posts
   
    for post in all_posts_with_tag:

        post.has_tags.remove(tag)
        # PAM: i added and commit a post to session here to resolve this Error:

        # sqlalchemy.orm.exc.StaleDataError: DELETE statement on table 'posts_tags' expected to delete 2 row(s); Only 1 were matched.

        # PAM: seems if i delete a tag its ok it it doesnt have any posts , 
        # but if i delete multiple ralations between them in post_tags before 
        # commiting to session, only the first has an effect and the rest dont get treated the same way?

        db.session.add(post)
        db.session.commit()

    # DELETE the tag
    db.session.delete(tag)
    db.session.commit()
    
    return redirect("/tags")



