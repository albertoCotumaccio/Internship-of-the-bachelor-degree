from django import forms
from .models import Ricetta, Tag, Ingrediente, Portata, Contenuto, Impianto, Chef

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate





"""
class RegisterForm(forms.Form):
	username = forms.CharField(label='Username', min_length=4, max_length=150)
	email = forms.EmailField(label='Email')
	first_name = forms.CharField(label='Nome')
	last_name = forms.CharField(label='Cognome')
	password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
	password2 = forms.CharField(label='Conferma password', widget=forms.PasswordInput)
	impianto = forms.ModelChoiceField(label='Impianto',queryset=Impianto.objects.all())

	class Meta:
		model = User,
		fields = [
			'username',
			'email',
			'first_name',
			'last_name',
			'password1',
			'password2',
			'impianto'
		]

	def clean_username(self):
		username = self.cleaned_data['username']
		r = User.objects.filter(username=username)
		if r.count():
			raise  ValidationError("Username già esistente")
		return username

	def clean_email(self):
		email = self.cleaned_data['email'].lower()
		r = User.objects.filter(email=email)
		if r.count():
			raise  ValidationError("Email già esistente")
		return email

	def clean_password2(self):
		password1 = self.cleaned_data.get('password1')
		password2 = self.cleaned_data.get('password2')

		if password1 and password2 and password1 != password2:
			raise ValidationError("Le password non corrispondono. Riprova")

		return password2


	def save(self, commit=True):
		user = User.objects.create_user(
			self.cleaned_data['username'],
			self.cleaned_data['email'],
			self.cleaned_data['password1']
			)

		user.first_name = self.cleaned_data['first_name']
		user.last_name = self.cleaned_data['last_name']
		impiantoStr = str(self.cleaned_data['impianto'])
		impianto = Impianto.objects.get(nome=impiantoStr) 
		chef = Chef(impianto=impianto,user=user)
		chef.save()
		gruppo = Group.objects.get(name="Chef") 
		gruppo.user_set.add(user)
		user.save()

		return user
"""


class UserLoginForm(forms.Form):
	username = forms.CharField()
	password = forms.CharField(widget=forms.PasswordInput)

	#invocato ogni volta che il form è submitted e si assura che i dati sono quelli che volevo
	def clean(self, *args, **kwargs):
		username = self.cleaned_data.get('username')
		password = self.cleaned_data.get('password')

		if username and password:
			try:
				user = User.objects.get(username__iexact=username)
			except User.DoesNotExist:
				raise forms.ValidationError('Utente inesistente')
			
			if not user.check_password(password):
				raise ValidationError('Password non corretta')
			if not user.is_active:
				raise ValidationError('Utente non attivo')

		return super(UserLoginForm, self).clean(*args, **kwargs)


