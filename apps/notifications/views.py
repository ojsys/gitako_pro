from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class NotificationListView(LoginRequiredMixin, TemplateView):
    template_name = 'notifications/list.html'