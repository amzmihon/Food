from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from datetime import date, timedelta
from .models import Member, MealPrice, MealRecord, Payment


def _admin_exists():
    """Check if any staff/superuser accounts exist."""
    return User.objects.filter(is_staff=True).exists()


def _redirect_non_staff(request):
    """Send non-admin users away from admin-only areas."""
    if not request.user.is_staff:
        messages.error(request, "Admin access required.")
        return redirect('my_meals')
    return None


def login_view(request):
    """Authenticate admin/staff or regular users."""
    if request.user.is_authenticated:
        return redirect('dashboard') if request.user.is_staff else redirect('my_meals')

    next_url = request.GET.get('next', '')
    admin_present = _admin_exists()

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', next_url)

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")

            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure()
            ):
                return redirect(next_url)
            return redirect('dashboard') if user.is_staff else redirect('my_meals')

        messages.error(request, "Invalid username or password.")

    return render(request, 'login.html', {
        'next': next_url,
        'allow_admin_signup': not admin_present
    })


def admin_signup(request):
    """Allow creating the very first admin account."""
    if _admin_exists():
        messages.info(request, "An admin already exists. Please log in.")
        return redirect('login')

    if request.user.is_authenticated:
        return redirect('dashboard') if request.user.is_staff else redirect('my_meals')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not username or not password1:
            messages.error(request, "Username and password are required.")
        elif password1 != password2:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
        else:
            User.objects.create_superuser(username=username, email=email, password=password1)
            messages.success(request, "Admin account created. Please log in.")
            return redirect('login')

    return render(request, 'admin_signup.html')


@login_required
def logout_view(request):
    """Log the current user out."""
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')


@login_required
def my_meals(request):
    """Allow a user to view and set their own meal decision before 10:30 AM."""
    member = getattr(request.user, 'member_profile', None)
    today = timezone.localdate()
    now = timezone.localtime()
    deadline = now.replace(hour=10, minute=30, second=0, microsecond=0)
    locked = now >= deadline

    if request.method == 'POST':
        if not member:
            messages.error(request, "Your account is not linked to a member. Please contact an admin.")
            return redirect('my_meals')

        if locked:
            messages.error(request, "Changes are locked after 10:30 AM.")
            return redirect('my_meals')

        decision = request.POST.get('decision')
        if decision not in ('eat', 'skip'):
            messages.error(request, "Invalid meal selection.")
            return redirect('my_meals')

        record, _ = MealRecord.objects.get_or_create(member=member, date=today)
        record.ate_meal = decision == 'eat'
        record.save()
        status_label = "eating" if record.ate_meal else "skipping"
        messages.success(request, f"You are marked as {status_label} today.")
        return redirect('my_meals')

    today_record = None
    if member:
        today_record = MealRecord.objects.filter(member=member, date=today).first()

    week_start = Member.get_week_start(today)
    week_days = [week_start + timedelta(days=i) for i in range(7)]
    week_records = {}
    if member:
        week_records = {
            rec.date: rec
            for rec in MealRecord.objects.filter(
                member=member,
                date__gte=week_start,
                date__lte=week_start + timedelta(days=6)
            )
        }
    week_rows = [{'date': day, 'record': week_records.get(day)} for day in week_days]

    context = {
        'member': member,
        'today': today,
        'today_record': today_record,
        'locked': locked,
        'deadline': deadline,
        'current_time': now,
        'week_start': week_start,
        'week_end': week_start + timedelta(days=6),
        'week_days': week_days,
        'week_records': week_records,
        'week_rows': week_rows,
        'week_meals': member.get_weekly_meals(week_start) if member else 0,
        'week_total': member.get_weekly_total_bill(week_start) if member else 0,
        'unpaid_balance': member.get_unpaid_balance(week_start) if member else 0,
        'price_today': MealPrice.get_price_for_date(today) if member else 0,
    }

    return render(request, 'my_meals.html', context)


@login_required
def dashboard(request):
    """Main dashboard showing weekly summary"""
    redirect_resp = _redirect_non_staff(request)
    if redirect_resp:
        return redirect_resp

    # Get current week start (Saturday)
    today = date.today()
    week_start = Member.get_week_start(today)
    week_end = week_start + timedelta(days=6)
    
    # Get all active members
    members = Member.objects.filter(is_active=True)
    
    # Prepare data for each member
    member_data = []
    for member in members:
        meals = member.get_weekly_meals(week_start)
        total_bill = member.get_weekly_total_bill(week_start)
        paid = member.get_total_paid()
        unpaid = total_bill - paid
        
        member_data.append({
            'serial': member.serial_number,
            'name': member.name,
            'meals': meals,
            'total_bill': total_bill,
            'paid': paid,
            'unpaid': unpaid
        })
    
    context = {
        'member_data': member_data,
        'week_start': week_start,
        'week_end': week_end,
        'today': today
    }
    
    return render(request, 'dashboard.html', context)


@login_required
def daily_meals(request):
    """Interface for marking daily meals"""
    redirect_resp = _redirect_non_staff(request)
    if redirect_resp:
        return redirect_resp

    # Get week offset from URL parameter (0 = current week, -1 = previous, +1 = next)
    week_offset = int(request.GET.get('week', 0))
    
    # Get current week
    today = date.today()
    current_week_start = Member.get_week_start(today)
    week_start = current_week_start + timedelta(weeks=week_offset)
    
    # Generate 7 days of the week
    week_days = [week_start + timedelta(days=i) for i in range(7)]
    
    # Get all active members
    members = Member.objects.filter(is_active=True)
    
    # Prepare meal records matrix
    meal_matrix = []
    for member in members:
        row = {'member': member, 'meals': []}
        for day in week_days:
            try:
                record = MealRecord.objects.get(member=member, date=day)
            except MealRecord.DoesNotExist:
                record = None
            row['meals'].append({
                'date': day,
                'record': record,
                'ate': record.ate_meal if record else False
            })
        meal_matrix.append(row)
    
    # Handle POST request (toggling meal status)
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        meal_date = request.POST.get('date')
        
        if member_id and meal_date:
            member = get_object_or_404(Member, id=member_id)
            meal_date = date.fromisoformat(meal_date)
            
            # Toggle meal status
            record, created = MealRecord.objects.get_or_create(
                member=member,
                date=meal_date,
                defaults={'ate_meal': True}
            )
            
            if not created:
                record.ate_meal = not record.ate_meal
                record.save()
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Return JSON response for AJAX
                return JsonResponse({
                    'success': True,
                    'ate': record.ate_meal,
                    'message': f"Updated meal for {member.name} on {meal_date.strftime('%b %d, %Y')}"
                })
            else:
                # Traditional form submission - redirect with message
                messages.success(request, f"Updated meal for {member.name} on {meal_date}")
                return redirect('daily_meals')
    
    context = {
        'week_days': week_days,
        'meal_matrix': meal_matrix,
        'week_start': week_start,
        'week_end': week_start + timedelta(days=6),
        'today': today,
        'week_offset': week_offset,
        'is_current_week': week_offset == 0
    }
    
    return render(request, 'daily_meals.html', context)


@login_required
def manage_price(request):
    """Manage meal prices"""
    redirect_resp = _redirect_non_staff(request)
    if redirect_resp:
        return redirect_resp

    if request.method == 'POST':
        price_date = request.POST.get('date')
        price_amount = request.POST.get('price')
        
        if price_date and price_amount:
            price_date = date.fromisoformat(price_date)
            price_obj, created = MealPrice.objects.get_or_create(
                date=price_date,
                defaults={'price_per_meal': price_amount}
            )
            
            if not created:
                price_obj.price_per_meal = price_amount
                price_obj.save()
                messages.success(request, f"Updated price for {price_date}")
            else:
                messages.success(request, f"Added price for {price_date}")
            
            return redirect('manage_price')
    
    # Get recent prices
    recent_prices = MealPrice.objects.all()[:30]
    
    context = {
        'recent_prices': recent_prices,
        'today': date.today()
    }
    
    return render(request, 'manage_price.html', context)


@login_required
def manage_payments(request):
    """Manage payments"""
    redirect_resp = _redirect_non_staff(request)
    if redirect_resp:
        return redirect_resp

    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        amount = request.POST.get('amount')
        payment_date = request.POST.get('date')
        note = request.POST.get('note', '')
        
        if member_id and amount:
            member = get_object_or_404(Member, id=member_id)
            payment_date = date.fromisoformat(payment_date) if payment_date else date.today()
            
            Payment.objects.create(
                member=member,
                amount=amount,
                payment_date=payment_date,
                note=note
            )
            
            messages.success(request, f"Payment recorded for {member.name}")
            return redirect('manage_payments')
    
    # Get all members and recent payments
    members = Member.objects.filter(is_active=True)
    recent_payments = Payment.objects.all()[:20]
    
    context = {
        'members': members,
        'recent_payments': recent_payments,
        'today': date.today()
    }
    
    return render(request, 'manage_payments.html', context)


@login_required
def manage_members(request):
    """Manage members"""
    redirect_resp = _redirect_non_staff(request)
    if redirect_resp:
        return redirect_resp

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            name = request.POST.get('name')
            serial = request.POST.get('serial_number')
            
            if name and serial:
                Member.objects.create(
                    name=name,
                    serial_number=serial,
                    is_active=True
                )
                messages.success(request, f"Added member: {name}")
        
        elif action == 'edit':
            member_id = request.POST.get('member_id')
            new_name = request.POST.get('name')
            
            if member_id and new_name:
                member = get_object_or_404(Member, id=member_id)
                old_name = member.name
                member.name = new_name
                member.save()
                messages.success(request, f"Updated member name from '{old_name}' to '{new_name}'")
        
        elif action == 'toggle':
            member_id = request.POST.get('member_id')
            member = get_object_or_404(Member, id=member_id)
            member.is_active = not member.is_active
            member.save()
            status = "activated" if member.is_active else "deactivated"
            messages.success(request, f"{member.name} {status}")
        
        return redirect('manage_members')
    
    # Get all members
    all_members = Member.objects.all()
    
    context = {
        'members': all_members
    }
    
    return render(request, 'manage_members.html', context)
