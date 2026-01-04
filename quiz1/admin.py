from django.contrib import admin
from django.forms import ValidationError, BaseInlineFormSet
from .models import Category, Quiz, Question, Choice,UserScore


# Custom Inline FormSet for Validation
class ChoiceInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        correct_choices = 0

        for form in self.forms:
            if not form.cleaned_data.get('DELETE', False):  # Ignore deleted forms
                if form.cleaned_data.get('is_correct', False):
                    correct_choices += 1

        if correct_choices == 0:
            raise ValidationError("You must mark one option as correct.")
        elif correct_choices > 1:
            raise ValidationError("Only one option can be marked as correct.")


# Inline for Choices
class ChoiceInline(admin.TabularInline):
    model = Choice
    formset = ChoiceInlineFormSet  # Attach the custom formset
    extra = 4  # Allow exactly 4 options


# Admin for Questions
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz')  # Show question and quiz in the list view
    inlines = [ChoiceInline]  # Attach choices inline with questions


# Register Admin Classes
admin.site.register(Category)
admin.site.register(Quiz)
admin.site.register(Question, QuestionAdmin)
admin.site.register(UserScore)
