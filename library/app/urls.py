from django.urls import path,include
from . import views
urlpatterns = [
   
   path('', views.landing, name='landing'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('browse_collections/', views.browse_collections, name='browse_collections'),
    path('check_username/', views.check_username, name='check_username'),
    path('check_email/', views.check_email, name='check_email'),

    path('admin_users/', views.admin_users, name='admin_users'),
    path('admin_users_add/', views.admin_add_user, name='admin_add_user'),
    path('admin_users_delete/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    path('admin_users_edit/<int:user_id>/', views.admin_edit_user, name='admin_edit_user'),

     # Books Management
    path('admin_books/', views.admin_books, name='admin_books'),
    path('admin_books_add/', views.admin_add_book, name='admin_add_book'),
    path('admin_books_edit/<int:book_id>/', views.admin_edit_book, name='admin_edit_book'),
    path('admin_books_delete/<int:book_id>/', views.admin_delete_book, name='admin_delete_book'),


    path('admin_categories/', views.admin_categories, name='admin_categories'),
    path('admin_categories/add/', views.admin_add_category, name='admin_add_category'),
    path('admin_categories/edit/<int:category_id>/', views.admin_edit_category, name='admin_edit_category'),
    path('admin_categories/delete/<int:category_id>/', views.admin_delete_category, name='admin_delete_category'),


   path('browse/', views.browse_collection, name='browse_collection'),
    path('borrow/<int:book_id>/', views.borrow_book, name='borrow_book'),
    path('wishlist', views.wishlist, name='wishlist'),
    path('wishlist/toggle/<int:book_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/remove/<int:book_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/count/', views.get_wishlist_count, name='get_wishlist_count'), 

    path('admin_borrow_records/', views.admin_borrow_records, name='admin_borrow_records'),
    path('admin/borrow-record/<int:record_id>/', views.admin_borrow_record_detail, name='admin_borrow_record_detail'),
    path('admin/borrow-record/<int:record_id>/return/', views.admin_process_return, name='admin_process_return'),
    path('admin/borrow-record/<int:record_id>/remind/', views.admin_send_reminder, name='admin_send_reminder'),
    
    path('my-borrowed-books/', views.my_borrowed_books, name='my_borrowed_books'),
    path('borrow-record/<int:record_id>/renew/', views.renew_book, name='renew_book'),
    path('borrow-history/', views.borrow_history, name='borrow_history'),
]