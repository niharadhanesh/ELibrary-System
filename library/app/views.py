from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib.auth.decorators import login_required

def landing(request):
    return render(request, "landing.html")


def browse_collections(request):
    return render(request, "browse_collections.html")


# ======================
# LOGIN VIEW
# ======================
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # ✅ Redirect based on user type
            if user.is_superuser:
                return redirect("admin_dashboard")  # Admin dashboard
            else:
                return redirect("user_dashboard")   # Normal user dashboard
        else:
            # Invalid credentials
            messages.error(request, "Invalid username or password. Please try again.")
            return redirect(request.META.get('HTTP_REFERER'))

    return render(request, "login.html")

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings
from django.http import JsonResponse

# ======================
# REGISTER VIEW
# ======================
def register(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Password match check
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect(request.META.get('HTTP_REFERER'))

        # Username/email already exists check
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect(request.META.get('HTTP_REFERER'))
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect(request.META.get('HTTP_REFERER'))

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.first_name = name
        user.save()

        # Send confirmation email
        subject = "Welcome to E-Library!"
        message = f"""
Hello {name},

🎉 Your E-Library account has been successfully created!

Here are your login details:
---------------------------------
Username: {username}
Password: {password1}
---------------------------------

You can now log in and explore the E-Library platform.

Thank you for joining us! 📚

Best regards,  
E-Library Team
"""
        email_message = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
        email_message.send(fail_silently=True)

        messages.success(request, "Account created successfully! Login details have been sent to your email.")
        return redirect(request.META.get('HTTP_REFERER'))

    return render(request, "register.html")


# ======================
# AJAX CHECKS
# ======================
def check_username(request):
    username = request.GET.get('username')
    exists = User.objects.filter(username=username).exists()
    return JsonResponse({'exists': exists})

def check_email(request):
    email = request.GET.get('email')
    exists = User.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})


@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, "You are not authorized to view this page.")
        return redirect("login")
    return render(request, "admin_dashboard.html")


@login_required
def user_dashboard(request):
    if request.user.is_superuser:
        return redirect("admin_dashboard")
    return render(request, "user_dashboard.html")


def logout_view(request):
    logout(request)  # logs out the user
    return redirect("landing")  # replace 'landing' with your landing page URL name

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.mail import EmailMessage
from django.conf import settings

# ====================== 
# CHECK IF USER IS ADMIN
# ====================== 
def is_admin(user):
    return user.is_staff or user.is_superuser

# ====================== 
# ADMIN USERS LIST VIEW
# ====================== 
@login_required
@user_passes_test(is_admin)
def admin_users(request):
    # Get all users
    users_list = User.objects.all().order_by('-date_joined')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users_list = users_list.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        users_list = users_list.filter(is_active=True)
    elif status_filter == 'inactive':
        users_list = users_list.filter(is_active=False)
    
    # Role filter
    role_filter = request.GET.get('role', '')
    if role_filter == 'staff':
        users_list = users_list.filter(is_staff=True)
    elif role_filter == 'user':
        users_list = users_list.filter(is_staff=False)
    
    # Pagination
    paginator = Paginator(users_list, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)
    
    # Statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    
    context = {
        'users': users,
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'search_query': search_query,
        'status_filter': status_filter,
        'role_filter': role_filter,
    }
    
    return render(request, 'admin_users.html', context)

# ====================== 
# ADMIN ADD USER VIEW
# ====================== 
@login_required
@user_passes_test(is_admin)
def admin_add_user(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        is_staff = request.POST.get('is_staff') == 'on'
        
        # Validation
        if not all([name, username, email, password]):
            messages.error(request, "All fields are required.")
            return redirect('admin_users')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('admin_users')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('admin_users')
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            user.first_name = name
            user.is_staff = is_staff
            user.is_active = True
            user.save()
            
            # Send welcome email
            try:
                subject = "Welcome to E-Library!"
                message = f"""Hello {name},

🎉 Your E-Library account has been created by an administrator!

Here are your login details:
---------------------------------
Username: {username}
Password: {password}
---------------------------------

You can now log in and explore the E-Library platform.

Thank you for joining us! 📚

Best regards,
E-Library Team
"""
                email_message = EmailMessage(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email]
                )
                email_message.send(fail_silently=True)
            except:
                pass  # Email sending failure shouldn't stop user creation
            
            messages.success(request, f"User '{username}' added successfully!")
        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")
        
        return redirect('admin_users')
    
    return redirect('admin_users')

# ====================== 
# ADMIN EDIT USER VIEW
# ====================== 
@login_required
@user_passes_test(is_admin)
def admin_edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        is_staff = request.POST.get('is_staff') == 'on'
        new_password = request.POST.get('password', '').strip()
        
        # Validation
        if not name or not email:
            messages.error(request, "Name and email are required.")
            return redirect('admin_users')
        
        # Check if email is already used by another user
        if User.objects.filter(email=email).exclude(id=user_id).exists():
            messages.error(request, "Email already used by another user.")
            return redirect('admin_users')
        
        # Prevent removing staff status from yourself
        if user == request.user and not is_staff:
            messages.error(request, "You cannot remove staff status from yourself!")
            return redirect('admin_users')
        
        # Prevent deactivating yourself
        if user == request.user and not is_active:
            messages.error(request, "You cannot deactivate your own account!")
            return redirect('admin_users')
        
        try:
            # Update user
            user.first_name = name
            user.email = email
            user.is_active = is_active
            user.is_staff = is_staff
            
            # Update password if provided
            if new_password:
                user.set_password(new_password)
            
            user.save()
            messages.success(request, f"User '{user.username}' updated successfully!")
        except Exception as e:
            messages.error(request, f"Error updating user: {str(e)}")
        
        return redirect('admin_users')
    
    return redirect('admin_users')

# ====================== 
# ADMIN DELETE USER VIEW
# ====================== 
@login_required
@user_passes_test(is_admin)
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # Prevent deleting yourself
    if user == request.user:
        messages.error(request, "You cannot delete your own account!")
        return redirect('admin_users')
    
    # Prevent deleting superusers
    if user.is_superuser:
        messages.error(request, "Cannot delete superuser accounts!")
        return redirect('admin_users')
    
    try:
        username = user.username
        user.delete()
        messages.success(request, f"User '{username}' deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting user: {str(e)}")
    
    return redirect('admin_users')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import Book, Category  # Adjust based on your models

# ====================== 
# CHECK IF USER IS ADMIN
# ====================== 
def is_admin(user):
    return user.is_staff or user.is_superuser

# ====================== 
# ADMIN BOOKS LIST VIEW
# ====================== 
@login_required
@user_passes_test(is_admin)
def admin_books(request):
    # Get all books
    books_list = Book.objects.all().select_related('category').order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        books_list = books_list.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Category filter
    category_filter = request.GET.get('category', '')
    if category_filter:
        books_list = books_list.filter(category_id=category_filter)
    
    # Availability filter
    availability_filter = request.GET.get('availability', '')
    if availability_filter == 'available':
        books_list = books_list.filter(is_available=True)
    elif availability_filter == 'unavailable':
        books_list = books_list.filter(is_available=False)
    
    # Pagination
    paginator = Paginator(books_list, 12)  # Show 12 books per page
    page_number = request.GET.get('page')
    books = paginator.get_page(page_number)
    
    # Get all categories for filter dropdown
    categories = Category.objects.all().order_by('name')
    
    # Statistics
    total_books = Book.objects.count()
    available_books = Book.objects.filter(is_available=True).count()
    total_categories = Category.objects.count()
    total_authors = Book.objects.values('author').distinct().count()
    
    context = {
        'books': books,
        'categories': categories,
        'total_books': total_books,
        'available_books': available_books,
        'total_categories': total_categories,
        'total_authors': total_authors,
        'search_query': search_query,
        'category_filter': category_filter,
        'availability_filter': availability_filter,
    }
    
    return render(request, 'admin_books.html', context)

# ====================== 
# ADMIN ADD BOOK VIEW
# ====================== 
@login_required
@user_passes_test(is_admin)
def admin_add_book(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        author = request.POST.get('author', '').strip()
        isbn = request.POST.get('isbn', '').strip()
        category_id = request.POST.get('category')
        published_date = request.POST.get('published_date')
        pages = request.POST.get('pages')
        copies = request.POST.get('copies', 1)
        description = request.POST.get('description', '').strip()
        cover_image = request.FILES.get('cover_image')
        
        # Validation
        if not all([title, author, category_id]):
            messages.error(request, "Title, author, and category are required.")
            return redirect('admin_books')
        
        try:
            category = Category.objects.get(id=category_id)
            
            # Create book
            book = Book.objects.create(
                title=title,
                author=author,
                isbn=isbn,
                category=category,
                published_date=published_date if published_date else None,
                pages=int(pages) if pages else None,
                copies_available=int(copies),
                description=description,
                cover_image=cover_image,
                is_available=True
            )
            
            messages.success(request, f"Book '{title}' added successfully!")
        except Category.DoesNotExist:
            messages.error(request, "Invalid category selected.")
        except Exception as e:
            messages.error(request, f"Error adding book: {str(e)}")
        
        return redirect('admin_books')
    
    return redirect('admin_books')

# ====================== 
# ADMIN EDIT BOOK VIEW
# ====================== 
@login_required
@user_passes_test(is_admin)
def admin_edit_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        author = request.POST.get('author', '').strip()
        isbn = request.POST.get('isbn', '').strip()
        category_id = request.POST.get('category')
        published_date = request.POST.get('published_date')
        pages = request.POST.get('pages')
        copies = request.POST.get('copies', 0)
        description = request.POST.get('description', '').strip()
        is_available = request.POST.get('is_available') == 'on'
        cover_image = request.FILES.get('cover_image')
        
        # Validation
        if not all([title, author, category_id]):
            messages.error(request, "Title, author, and category are required.")
            return redirect('admin_books')
        
        try:
            category = Category.objects.get(id=category_id)
            
            # Update book
            book.title = title
            book.author = author
            book.isbn = isbn
            book.category = category
            book.published_date = published_date if published_date else None
            book.pages = int(pages) if pages else None
            book.copies_available = int(copies)
            book.description = description
            book.is_available = is_available
            
            # Update cover image only if new one is uploaded
            if cover_image:
                book.cover_image = cover_image
            
            book.save()
            
            messages.success(request, f"Book '{title}' updated successfully!")
        except Category.DoesNotExist:
            messages.error(request, "Invalid category selected.")
        except Exception as e:
            messages.error(request, f"Error updating book: {str(e)}")
        
        return redirect('admin_books')
    
    return redirect('admin_books')

# ====================== 
# ADMIN DELETE BOOK VIEW
# ====================== 
@login_required
@user_passes_test(is_admin)
def admin_delete_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    
    try:
        title = book.title
        
        # Delete cover image if exists
        if book.cover_image:
            book.cover_image.delete()
        
        book.delete()
        messages.success(request, f"Book '{title}' deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting book: {str(e)}")
    
    return redirect('admin_books')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count
from .models import Category, Book

# ====================== 
# CHECK IF USER IS ADMIN
# ====================== 
def is_admin(user):
    return user.is_staff or user.is_superuser

# ====================== 
# ADMIN CATEGORIES LIST VIEW
# ====================== 
@login_required
@user_passes_test(is_admin)
def admin_categories(request):
    # Get all categories with book count
    categories_list = Category.objects.all().annotate(
        book_count=Count('books')
    ).order_by('name')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        categories_list = categories_list.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Statistics
    total_categories = Category.objects.count()
    total_books = Book.objects.count()
    
    context = {
        'categories': categories_list,
        'total_categories': total_categories,
        'total_books': total_books,
        'search_query': search_query,
    }
    
    return render(request, 'admin_categories.html', context)

# ====================== 
# ADMIN ADD CATEGORY VIEW
# ====================== 
@login_required
@user_passes_test(is_admin)
def admin_add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        # Validation
        if not name:
            messages.error(request, "Category name is required.")
            return redirect('admin_categories')
        
        # Check if category already exists
        if Category.objects.filter(name__iexact=name).exists():
            messages.error(request, f"Category '{name}' already exists.")
            return redirect('admin_categories')
        
        try:
            # Create category
            category = Category.objects.create(
                name=name,
                description=description if description else None
            )
            
            messages.success(request, f"Category '{name}' added successfully!")
        except Exception as e:
            messages.error(request, f"Error adding category: {str(e)}")
        
        return redirect('admin_categories')
    
    return redirect('admin_categories')

# ====================== 
# ADMIN EDIT CATEGORY VIEW
# ====================== 
@login_required
@user_passes_test(is_admin)
def admin_edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        # Validation
        if not name:
            messages.error(request, "Category name is required.")
            return redirect('admin_categories')
        
        # Check if another category with same name exists
        existing = Category.objects.filter(name__iexact=name).exclude(id=category_id)
        if existing.exists():
            messages.error(request, f"Category '{name}' already exists.")
            return redirect('admin_categories')
        
        try:
            # Update category
            category.name = name
            category.description = description if description else None
            category.save()
            
            messages.success(request, f"Category '{name}' updated successfully!")
        except Exception as e:
            messages.error(request, f"Error updating category: {str(e)}")
        
        return redirect('admin_categories')
    
    return redirect('admin_categories')

# ====================== 
# ADMIN DELETE CATEGORY VIEW
# ====================== 
@login_required
@user_passes_test(is_admin)
def admin_delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    try:
        name = category.name
        book_count = category.books.count()
        
        # Delete category (books will have category set to NULL due to SET_NULL)
        category.delete()
        
        if book_count > 0:
            messages.warning(
                request, 
                f"Category '{name}' deleted. {book_count} book(s) no longer have a category assigned."
            )
        else:
            messages.success(request, f"Category '{name}' deleted successfully!")
            
    except Exception as e:
        messages.error(request, f"Error deleting category: {str(e)}")
    
    return redirect('admin_categories')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta
from .models import Book, Category, BorrowRecord, Wishlist

# ====================== 
# USER BROWSE COLLECTION VIEW (UPDATED WITH WISHLIST)
# ====================== 
@login_required
def browse_collection(request):
    """
    Display all available books to users with search, filter, and sort functionality
    """
    # Get all books (show only available books by default to users)
    books_list = Book.objects.all().select_related('category').order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        books_list = books_list.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Category filter
    category_filter = request.GET.get('category', '')
    if category_filter:
        books_list = books_list.filter(category_id=category_filter)
    
    # Availability filter
    availability_filter = request.GET.get('availability', '')
    if availability_filter == 'available':
        books_list = books_list.filter(is_available=True, copies_available__gt=0)
    elif availability_filter == 'unavailable':
        books_list = books_list.filter(Q(is_available=False) | Q(copies_available=0))
    
    # Sort functionality
    sort_by = request.GET.get('sort', '')
    if sort_by:
        if sort_by in ['title', '-title', 'author', '-author', 'published_date', '-published_date']:
            books_list = books_list.order_by(sort_by)
    
    # Pagination (16 books per page for better grid layout)
    paginator = Paginator(books_list, 16)
    page_number = request.GET.get('page')
    books = paginator.get_page(page_number)
    
    # Get user's wishlist book IDs for displaying heart icon state
    wishlist_book_ids = []
    if request.user.is_authenticated:
        wishlist_book_ids = list(
            Wishlist.objects.filter(user=request.user).values_list('book_id', flat=True)
        )
    
    # Get all categories for filter dropdown
    categories = Category.objects.all().order_by('name')
    
    # Statistics
    total_books = Book.objects.count()
    available_books = Book.objects.filter(is_available=True, copies_available__gt=0).count()
    total_categories = Category.objects.count()
    total_authors = Book.objects.values('author').distinct().count()
    
    # Calculate dates for modal
    today = datetime.now().date()
    due_date = today + timedelta(days=14)
    
    context = {
        'books': books,
        'categories': categories,
        'total_books': total_books,
        'available_books': available_books,
        'total_categories': total_categories,
        'total_authors': total_authors,
        'search_query': search_query,
        'category_filter': category_filter,
        'availability_filter': availability_filter,
        'sort_by': sort_by,
        'today_date': today.strftime('%B %d, %Y'),
        'due_date': due_date.strftime('%B %d, %Y'),
        'wishlist_book_ids': wishlist_book_ids,  # NEW: Pass wishlist IDs to template
    }
    
    return render(request, 'browse_collection.html', context)


# ====================== 
# BORROW BOOK VIEW
# ====================== 
@login_required
def borrow_book(request, book_id):
    """
    Handle book borrowing request
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('browse_collection')
    
    book = get_object_or_404(Book, id=book_id)
    
    # Check if user agreed to terms
    agree_terms = request.POST.get('agree_terms')
    if not agree_terms:
        messages.error(request, "You must agree to the borrowing terms and conditions.")
        return redirect('browse_collection')
    
    # Check if book is available
    if not book.is_borrowable:
        messages.error(request, f"Sorry, '{book.title}' is not available for borrowing at the moment.")
        return redirect('browse_collection')
    
    # Check if user already has this book borrowed
    existing_borrow = BorrowRecord.objects.filter(
        user=request.user,
        book=book,
        status__in=['borrowed', 'overdue']
    ).exists()
    
    if existing_borrow:
        messages.warning(request, f"You have already borrowed '{book.title}'. Please return it before borrowing again.")
        return redirect('browse_collection')
    
    # Check if user has reached maximum borrow limit (e.g., 5 books)
    active_borrows = BorrowRecord.objects.filter(
        user=request.user,
        status__in=['borrowed', 'overdue']
    ).count()
    
    MAX_BORROW_LIMIT = 5
    if active_borrows >= MAX_BORROW_LIMIT:
        messages.error(request, f"You have reached the maximum borrow limit of {MAX_BORROW_LIMIT} books. Please return some books first.")
        return redirect('my_borrowed_books')
    
    # Check for overdue books
    overdue_books = BorrowRecord.objects.filter(
        user=request.user,
        status='overdue'
    ).exists()
    
    if overdue_books:
        messages.error(request, "You have overdue books. Please return them before borrowing new books.")
        return redirect('browse_collection')
    
    try:
        # Create borrow record
        due_date = datetime.now().date() + timedelta(days=14)  # 14 days borrowing period
        
        BorrowRecord.objects.create(
            user=request.user,
            book=book,
            due_date=due_date,
            status='borrowed'
        )
        
        # Update book availability
        book.copies_available -= 1
        if book.copies_available == 0:
            book.is_available = False
        book.save()
        
        messages.success(
            request, 
            f"✅ Successfully borrowed '{book.title}'! Please return it by {due_date.strftime('%B %d, %Y')}."
        )
        
    except Exception as e:
        messages.error(request, f"Error borrowing book: {str(e)}")
        return redirect('browse_collection')
    
    return redirect('browse_collection')


# ====================== 
# TOGGLE WISHLIST (AJAX) - NEW
# ====================== 
@login_required
@require_POST
def toggle_wishlist(request, book_id):
    """
    Add or remove book from wishlist (AJAX endpoint)
    Returns JSON response for seamless user experience
    """
    try:
        book = get_object_or_404(Book, id=book_id)
        
        # Check if book is already in wishlist
        wishlist_item = Wishlist.objects.filter(user=request.user, book=book).first()
        
        if wishlist_item:
            # Remove from wishlist
            wishlist_item.delete()
            return JsonResponse({
                'success': True,
                'action': 'removed',
                'message': f"'{book.title}' removed from wishlist"
            })
        else:
            # Add to wishlist
            Wishlist.objects.create(user=request.user, book=book)
            return JsonResponse({
                'success': True,
                'action': 'added',
                'message': f"'{book.title}' added to wishlist"
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


# ====================== 
# VIEW WISHLIST PAGE - NEW
# ====================== 
@login_required
def wishlist(request):
    """
    Display user's wishlist with all saved books
    """
    # Get all wishlist items for current user
    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related('book', 'book__category').order_by('-added_at')
    
    # Pagination (12 books per page for wishlist)
    paginator = Paginator(wishlist_items, 12)
    page_number = request.GET.get('page')
    wishlist = paginator.get_page(page_number)
    
    # Calculate dates for modal
    today = datetime.now().date()
    due_date = today + timedelta(days=14)
    
    context = {
        'wishlist': wishlist,
        'total_items': wishlist_items.count(),
        'today_date': today.strftime('%B %d, %Y'),
        'due_date': due_date.strftime('%B %d, %Y'),
    }
    
    return render(request, 'wishlist.html', context)


# ====================== 
# REMOVE FROM WISHLIST - NEW
# ====================== 
@login_required
@require_POST
def remove_from_wishlist(request, book_id):
    """
    Remove book from wishlist (used on wishlist page with confirmation)
    """
    try:
        book = get_object_or_404(Book, id=book_id)
        wishlist_item = Wishlist.objects.filter(user=request.user, book=book).first()
        
        if wishlist_item:
            book_title = book.title
            wishlist_item.delete()
            messages.success(request, f"'{book_title}' removed from your wishlist.")
        else:
            messages.info(request, "This book is not in your wishlist.")
    
    except Exception as e:
        messages.error(request, f"Error removing book from wishlist: {str(e)}")
    
    return redirect('wishlist')


# ====================== 
# GET WISHLIST COUNT (OPTIONAL - FOR NAVBAR BADGE) - NEW
# ====================== 
@login_required
def get_wishlist_count(request):
    """
    Get wishlist count for displaying in navbar badge (optional feature)
    Can be called via AJAX to update count dynamically
    """
    count = Wishlist.objects.filter(user=request.user).count()
    return JsonResponse({'count': count})

from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta
import csv
from .models import BorrowRecord, Book

# ====================== 
# ADMIN BORROW RECORDS VIEW
# ====================== 
@staff_member_required
def admin_borrow_records(request):
    """
    Admin view to display all borrow records with detailed user and book information
    """
    # Get all borrow records with related user and book data
    records_list = BorrowRecord.objects.all().select_related('user', 'book', 'book__category').order_by('-borrow_date')
    
    # Search by user
    user_search = request.GET.get('user_search', '')
    if user_search:
        records_list = records_list.filter(
            Q(user__username__icontains=user_search) |
            Q(user__email__icontains=user_search) |
            Q(user__first_name__icontains=user_search) |
            Q(user__last_name__icontains=user_search) |
            Q(id__icontains=user_search)
        )
    
    # Search by book
    book_search = request.GET.get('book_search', '')
    if book_search:
        records_list = records_list.filter(
            Q(book__title__icontains=book_search) |
            Q(book__author__icontains=book_search) |
            Q(book__isbn__icontains=book_search)
        )
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        records_list = records_list.filter(status=status)
    
    # Sort functionality
    sort_by = request.GET.get('sort', '-borrow_date')
    valid_sorts = [
        'borrow_date', '-borrow_date', 
        'due_date', '-due_date',
        'return_date', '-return_date',
        'user__username', '-user__username',
        'book__title', '-book__title'
    ]
    if sort_by in valid_sorts:
        records_list = records_list.order_by(sort_by)
    
    # Handle CSV export
    if request.GET.get('export') == 'csv':
        return export_borrow_records_csv(records_list)
    
    # Pagination (20 records per page)
    paginator = Paginator(records_list, 20)
    page_number = request.GET.get('page')
    records = paginator.get_page(page_number)
    
    # Statistics
    total_records = BorrowRecord.objects.count()
    active_borrows = BorrowRecord.objects.filter(status__in=['borrowed', 'overdue']).count()
    overdue_count = BorrowRecord.objects.filter(status='overdue').count()
    returned_count = BorrowRecord.objects.filter(status='returned').count()
    
    context = {
        'records': records,
        'total_records': total_records,
        'active_borrows': active_borrows,
        'overdue_count': overdue_count,
        'returned_count': returned_count,
        'user_search': user_search,
        'book_search': book_search,
        'status': status,
        'sort': sort_by,
    }
    
    return render(request, 'admin_borrow_records.html', context)


# ====================== 
# PROCESS RETURN (ADMIN)
# ====================== 
@staff_member_required
@require_POST
def admin_process_return(request, record_id):
    """
    Admin endpoint to process book return
    """
    try:
        record = get_object_or_404(BorrowRecord, id=record_id)
        
        if record.status == 'returned':
            return JsonResponse({
                'success': False,
                'message': 'This book has already been returned.'
            })
        
        # Calculate fine for overdue books
        today = datetime.now().date()
        fine_amount = 0
        
        if today > record.due_date:
            days_overdue = (today - record.due_date).days
            fine_amount = days_overdue * 1  # $1 per day
        
        # Update record
        record.return_date = today
        record.status = 'returned'
        record.fine_amount = fine_amount
        record.save()
        
        # Update book availability
        book = record.book
        book.copies_available += 1
        if book.copies_available > 0:
            book.is_available = True
        book.save()
        
        message = f'Book returned successfully!'
        if fine_amount > 0:
            message += f' Fine amount: ${fine_amount:.2f} ({days_overdue} days overdue)'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'fine_amount': fine_amount
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error processing return: {str(e)}'
        })


# ====================== 
# SEND REMINDER (ADMIN)
# ====================== 
@staff_member_required
@require_POST
def admin_send_reminder(request, record_id):
    """
    Admin endpoint to send overdue reminder to user
    """
    try:
        record = get_object_or_404(BorrowRecord, id=record_id)
        
        if record.status != 'overdue':
            return JsonResponse({
                'success': False,
                'message': 'This book is not overdue.'
            })
        
        # Calculate days overdue
        today = datetime.now().date()
        days_overdue = (today - record.due_date).days
        fine_amount = days_overdue * 1  # $1 per day
        
        # Here you would integrate with your email system
        # For now, we'll just return success
        # Example:
        # from django.core.mail import send_mail
        # send_mail(
        #     subject=f'Overdue Book Reminder - {record.book.title}',
        #     message=f'Dear {record.user.get_full_name()},\n\n'
        #             f'This is a reminder that your borrowed book "{record.book.title}" '
        #             f'is {days_overdue} days overdue.\n'
        #             f'Due date: {record.due_date.strftime("%B %d, %Y")}\n'
        #             f'Current fine: ${fine_amount:.2f}\n\n'
        #             f'Please return the book as soon as possible.\n\n'
        #             f'Best regards,\nLibrary Management',
        #     from_email='library@example.com',
        #     recipient_list=[record.user.email],
        # )
        
        return JsonResponse({
            'success': True,
            'message': f'Reminder email sent successfully to {record.user.email}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error sending reminder: {str(e)}'
        })


# ====================== 
# VIEW BORROW RECORD DETAILS (ADMIN)
# ====================== 
@staff_member_required
def admin_borrow_record_detail(request, record_id):
    """
    Admin view to see detailed information about a specific borrow record
    """
    record = get_object_or_404(BorrowRecord.objects.select_related('user', 'book', 'book__category'), id=record_id)
    
    # Calculate current fine if overdue
    current_fine = 0
    days_overdue = 0
    
    if record.status in ['borrowed', 'overdue']:
        today = datetime.now().date()
        if today > record.due_date:
            days_overdue = (today - record.due_date).days
            current_fine = days_overdue * 1  # $1 per day
    elif record.status == 'returned' and record.fine_amount:
        current_fine = record.fine_amount
    
    # Get user's borrow history
    user_borrow_history = BorrowRecord.objects.filter(user=record.user).exclude(id=record.id).order_by('-borrow_date')[:5]
    
    context = {
        'record': record,
        'current_fine': current_fine,
        'days_overdue': days_overdue,
        'user_borrow_history': user_borrow_history,
    }
    
    return render(request, 'admin_borrow_record_detail.html', context)


# ====================== 
# EXPORT BORROW RECORDS TO CSV
# ====================== 
def export_borrow_records_csv(queryset):
    """
    Export borrow records to CSV file
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="borrow_records_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Record ID',
        'User Name',
        'User Email',
        'Book Title',
        'Book Author',
        'Book ISBN',
        'Borrow Date',
        'Due Date',
        'Return Date',
        'Status',
        'Fine Amount'
    ])
    
    for record in queryset:
        writer.writerow([
            record.id,
            record.user.get_full_name() or record.user.username,
            record.user.email,
            record.book.title,
            record.book.author,
            record.book.isbn or 'N/A',
            record.borrow_date.strftime('%Y-%m-%d'),
            record.due_date.strftime('%Y-%m-%d'),
            record.return_date.strftime('%Y-%m-%d') if record.return_date else 'Not Returned',
            record.status.upper(),
            f'${record.fine_amount:.2f}' if record.fine_amount else '$0.00'
        ])
    
    return response



from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta
from .models import BorrowRecord

# ====================== 
# USER BORROWED BOOKS VIEW
# ====================== 
@login_required
def my_borrowed_books(request):
    """
    Display all borrowed books for the logged-in user
    """
    # Get all borrow records for the current user
    records = BorrowRecord.objects.filter(
        user=request.user
    ).select_related('book', 'book__category').order_by('-borrow_date')
    
    # Calculate additional information for each record
    today = datetime.now().date()
    
    for record in records:
        # Calculate days until due or days overdue
        if record.status != 'returned':
            if record.due_date >= today:
                record.days_until_due = (record.due_date - today).days
                record.days_overdue = 0
            else:
                record.days_until_due = 0
                record.days_overdue = (today - record.due_date).days
                # Calculate current fine for overdue books
                if not record.fine_amount:
                    record.fine_amount = record.days_overdue * 1  # $1 per day
        else:
            record.days_until_due = None
            record.days_overdue = 0
        
        # Check if book can be renewed (not overdue, not already renewed)
        record.can_renew = (
            record.status == 'borrowed' and 
            not hasattr(record, 'is_renewed') or not record.is_renewed
        )
    
    # Get statistics
    active_count = records.filter(status__in=['borrowed', 'overdue']).count()
    overdue_count = records.filter(status='overdue').count()
    returned_count = records.filter(status='returned').count()
    total_borrowed = records.count()
    
    # Get books due within 3 days
    due_soon_date = today + timedelta(days=3)
    due_soon_books = [r for r in records if r.status == 'borrowed' and r.due_date <= due_soon_date and r.due_date >= today]
    due_soon_count = len(due_soon_books)
    
    # Get overdue books
    overdue_books = [r for r in records if r.status == 'overdue']
    
    context = {
        'records': records,
        'active_count': active_count,
        'overdue_count': overdue_count,
        'returned_count': returned_count,
        'total_borrowed': total_borrowed,
        'due_soon_count': due_soon_count,
        'due_soon_books': due_soon_books,
        'overdue_books': overdue_books,
    }
    
    return render(request, 'my_borrowed_books.html', context)


# ====================== 
# RENEW BOOK VIEW
# ====================== 
@login_required
@require_POST
def renew_book(request, record_id):
    """
    Allow user to renew a borrowed book (extend due date by 14 days)
    """
    try:
        record = get_object_or_404(BorrowRecord, id=record_id, user=request.user)
        
        # Check if book is eligible for renewal
        if record.status == 'returned':
            return JsonResponse({
                'success': False,
                'message': 'This book has already been returned.'
            })
        
        if record.status == 'overdue':
            return JsonResponse({
                'success': False,
                'message': 'Cannot renew overdue books. Please return the book first.'
            })
        
        # Check if already renewed (you can add a field to track this)
        if hasattr(record, 'renewal_count') and record.renewal_count >= 1:
            return JsonResponse({
                'success': False,
                'message': 'This book has already been renewed once. Maximum renewals reached.'
            })
        
        # Extend due date by 14 days
        record.due_date = record.due_date + timedelta(days=14)
        
        # Track renewal (add this field to your model if needed)
        if not hasattr(record, 'renewal_count'):
            record.renewal_count = 0
        record.renewal_count += 1
        
        record.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Book renewed successfully! New due date: {record.due_date.strftime("%B %d, %Y")}',
            'new_due_date': record.due_date.strftime("%B %d, %Y")
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error renewing book: {str(e)}'
        })


# ====================== 
# BORROW HISTORY VIEW (OPTIONAL - MORE DETAILED)
# ====================== 
@login_required
def borrow_history(request):
    """
    Display complete borrow history with filters and statistics
    """
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    year_filter = request.GET.get('year', '')
    
    # Base queryset
    records = BorrowRecord.objects.filter(
        user=request.user
    ).select_related('book', 'book__category').order_by('-borrow_date')
    
    # Apply filters
    if status_filter:
        records = records.filter(status=status_filter)
    
    if year_filter:
        records = records.filter(borrow_date__year=year_filter)
    
    # Get available years for filter
    years = BorrowRecord.objects.filter(
        user=request.user
    ).dates('borrow_date', 'year').distinct()
    
    # Calculate statistics
    today = datetime.now().date()
    total_borrowed = BorrowRecord.objects.filter(user=request.user).count()
    currently_borrowed = BorrowRecord.objects.filter(
        user=request.user, 
        status__in=['borrowed', 'overdue']
    ).count()
    total_returned = BorrowRecord.objects.filter(
        user=request.user, 
        status='returned'
    ).count()
    total_fines = BorrowRecord.objects.filter(
        user=request.user
    ).aggregate(total=Sum('fine_amount'))['total'] or 0
    
    # Books read this year
    books_this_year = BorrowRecord.objects.filter(
        user=request.user,
        borrow_date__year=today.year
    ).count()
    
    # Most borrowed category
    from django.db.models import Count
    favorite_category = BorrowRecord.objects.filter(
        user=request.user
    ).values('book__category__name').annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    context = {
        'records': records,
        'years': years,
        'status_filter': status_filter,
        'year_filter': year_filter,
        'total_borrowed': total_borrowed,
        'currently_borrowed': currently_borrowed,
        'total_returned': total_returned,
        'total_fines': total_fines,
        'books_this_year': books_this_year,
        'favorite_category': favorite_category,
    }
    
    return render(request, 'borrow_history.html', context)