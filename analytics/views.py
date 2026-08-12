from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class AnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/reports_dashboard.html'
