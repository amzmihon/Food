from django.db import models
from django.utils import timezone
from datetime import date, timedelta


class Member(models.Model):
    """Model for tracking meal members"""
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    serial_number = models.IntegerField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['serial_number']

    def __str__(self):
        return f"{self.serial_number}. {self.name}"

    def get_weekly_meals(self, start_date=None):
        """Calculate total meals for current week"""
        if not start_date:
            start_date = self.get_week_start()
        end_date = start_date + timedelta(days=6)
        
        return MealRecord.objects.filter(
            member=self,
            date__gte=start_date,
            date__lte=end_date,
            ate_meal=True
        ).count()

    def get_weekly_total_bill(self, start_date=None):
        """Calculate total bill for current week"""
        if not start_date:
            start_date = self.get_week_start()
        end_date = start_date + timedelta(days=6)
        
        total = 0
        meals = MealRecord.objects.filter(
            member=self,
            date__gte=start_date,
            date__lte=end_date,
            ate_meal=True
        )
        
        for meal in meals:
            try:
                price = MealPrice.objects.get(date=meal.date)
                total += price.price_per_meal
            except MealPrice.DoesNotExist:
                pass
        
        return total

    def get_total_paid(self):
        """Calculate total amount paid by member"""
        return Payment.objects.filter(member=self).aggregate(
            total=models.Sum('amount')
        )['total'] or 0

    def get_unpaid_balance(self, start_date=None):
        """Calculate unpaid balance"""
        return self.get_weekly_total_bill(start_date) - self.get_total_paid()

    @staticmethod
    def get_week_start(ref_date=None):
        """Get the start date of the week (Saturday)"""
        if not ref_date:
            ref_date = date.today()
        # 5 = Saturday in Python's weekday() (0=Monday)
        days_since_saturday = (ref_date.weekday() + 2) % 7
        return ref_date - timedelta(days=days_since_saturday)


class MealPrice(models.Model):
    """Model for daily meal pricing"""
    date = models.DateField(unique=True)
    price_per_meal = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date}: {self.price_per_meal} Tk"

    @staticmethod
    def get_price_for_date(target_date):
        """Get price for a specific date, or use most recent price"""
        try:
            return MealPrice.objects.get(date=target_date).price_per_meal
        except MealPrice.DoesNotExist:
            # Get the most recent price before this date
            recent = MealPrice.objects.filter(date__lt=target_date).first()
            if recent:
                return recent.price_per_meal
            return 0


class MealRecord(models.Model):
    """Model for tracking daily meals"""
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='meal_records')
    date = models.DateField()
    ate_meal = models.BooleanField(default=False)
    meal_count = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['member', 'date']
        ordering = ['-date', 'member__serial_number']

    def __str__(self):
        status = "Ate" if self.ate_meal else "Didn't eat"
        return f"{self.member.name} - {self.date}: {status}"


class Payment(models.Model):
    """Model for tracking payments"""
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=date.today)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.member.name} - {self.amount} Tk on {self.payment_date}"
