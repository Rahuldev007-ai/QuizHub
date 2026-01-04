from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=20)
    

    def __str__(self):
        return self.name


class Quiz(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField(max_length=50)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    create_at = models.DateField(auto_now_add=True)
    update_at = models.DateField(auto_now=True)
    

    def __str__(self):
        return self.title


class Question(models.Model):
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'

    DIFFICULTY_CHOICES = [
        (EASY, 'Easy'),
        (MEDIUM, 'Medium'),
        (HARD, 'Hard'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    text = models.TextField()
    difficulty = models.CharField(
        max_length=6,
        choices=DIFFICULTY_CHOICES,
        default=EASY,  # Default to 'easy' if no difficulty is specified
    )

    def __str__(self):
        return self.text[:50]  # Shows the first 50 characters of the question text

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """
        Ensure only one choice per question is marked as correct.
        If this choice is marked correct, all other choices for the same question will be marked incorrect.
        """
        if self.is_correct:
            # Set other choices for this question as not correct
            Choice.objects.filter(question=self.question, is_correct=True).exclude(id=self.id).update(is_correct=False)
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.text} ({'Correct' if self.is_correct else 'Incorrect'})"

class UserScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()
    time_taken = models.DurationField()
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - Score: {self.score}"