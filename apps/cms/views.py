from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import (
    SiteSettings, TeamMember, Testimonial, Feature, 
    PricingPlan, FAQ, Office, HeroSection, ContactSubmission
)


class HomeView(TemplateView):
    template_name = 'cms/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['hero'] = HeroSection.objects.filter(page='home', is_active=True).first()
        context['features'] = Feature.objects.filter(is_active=True, feature_type='core')[:4]
        context['testimonials'] = Testimonial.objects.filter(is_active=True, is_featured=True)[:3]
        context['faqs'] = FAQ.objects.filter(is_active=True, category='Home')
        return context


class AboutView(TemplateView):
    template_name = 'cms/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['hero'] = HeroSection.objects.filter(page='about', is_active=True).first()
        context['team_members'] = TeamMember.objects.filter(is_active=True)
        return context


class FeaturesView(TemplateView):
    template_name = 'cms/features.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['hero'] = HeroSection.objects.filter(page='features', is_active=True).first()
        context['core_features'] = Feature.objects.filter(is_active=True, feature_type='core')
        context['advanced_features'] = Feature.objects.filter(is_active=True, feature_type='advanced')
        return context


class PricingView(TemplateView):
    template_name = 'cms/pricing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['hero'] = HeroSection.objects.filter(page='pricing', is_active=True).first()
        context['pricing_plans'] = PricingPlan.objects.filter(is_active=True)
        context['faqs'] = FAQ.objects.filter(is_active=True, category='Pricing')
        return context


class ContactView(TemplateView):
    template_name = 'cms/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['hero'] = HeroSection.objects.filter(page='contact', is_active=True).first()
        context['offices'] = Office.objects.filter(is_active=True)
        return context

    def post(self, request):
        # Create contact submission
        try:
            contact_submission = ContactSubmission.objects.create(
                first_name=request.POST.get('first_name', ''),
                last_name=request.POST.get('last_name', ''),
                email=request.POST.get('email', ''),
                phone=request.POST.get('phone', ''),
                company=request.POST.get('company', ''),
                inquiry_type=request.POST.get('inquiry_type', 'other'),
                message=request.POST.get('message', ''),
                newsletter_signup=bool(request.POST.get('newsletter'))
            )
            
            # Send notification email
            try:
                send_mail(
                    f'New Contact Submission: {contact_submission.get_inquiry_type_display()}',
                    f'From: {contact_submission.first_name} {contact_submission.last_name}\n'
                    f'Email: {contact_submission.email}\n'
                    f'Company: {contact_submission.company}\n'
                    f'Type: {contact_submission.get_inquiry_type_display()}\n\n'
                    f'Message:\n{contact_submission.message}',
                    settings.DEFAULT_FROM_EMAIL,
                    ['hello@gitako.com'],
                    fail_silently=True,
                )
            except:
                pass  # Don't fail if email sending fails
            
            messages.success(request, 'Thank you for your message! We will get back to you within 2 hours.')
        except Exception as e:
            messages.error(request, 'Sorry, there was an error submitting your message. Please try again.')

        return redirect('cms:contact')


class OfflineView(TemplateView):
    template_name = 'cms/offline.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['hero'] = HeroSection.objects.filter(page='offline', is_active=True).first()
        return context



