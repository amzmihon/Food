from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta
from .models import Member, MealPrice, MealRecord, Payment


def dashboard(request):
    """Main dashboard showing weekly summary"""
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


def daily_meals(request):
    """Interface for marking daily meals"""
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


def manage_price(request):
    """Manage meal prices"""
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


def manage_payments(request):
    """Manage payments"""
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


def manage_members(request):
    """Manage members"""
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
