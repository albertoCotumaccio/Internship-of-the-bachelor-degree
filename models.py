from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib import messages
import datetime
from datetime import date,timedelta
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from django.utils.timezone import get_current_timezone

# Create your models here.
class Tag(models.Model):
	nome = models.CharField(max_length=100, primary_key=True)
	posizione = models.PositiveIntegerField(validators= [MinValueValidator(1)])

	class Meta:
		ordering = ('posizione',)

	def __str__(self):
		return self.nome


class Allergene(models.Model):
	nome = models.CharField(max_length=100, primary_key=True)
	foto = models.ImageField(null=True, blank=True, upload_to="allergeni/")

	class Meta:
		ordering = ('nome',)

	def __str__(self):
		return self.nome



class Ingrediente(models.Model):
	nome_specifico = models.CharField(max_length=100)
	nome_generico = models.CharField(max_length=100, primary_key=True)
	listino = models.FloatField(validators=[MinValueValidator(0.0)])
	allergeni = models.ManyToManyField(Allergene, blank=True)
	energiaKcal = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	energiaKj = models.FloatField(default=0, validators=[MinValueValidator(0.0)]) #
	acqua = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	protAnim = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	protVeg = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	protTot = models.FloatField(default=0, validators=[MinValueValidator(0.0)]) #
	amido = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	glucidiSolub = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	glucidiTot = models.FloatField(default=0, validators=[MinValueValidator(0.0)]) #
	lipidiTot = models.FloatField(default=0, validators=[MinValueValidator(0.0)]) #
	saturi = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	monoins = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	polins = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	acidoOleico = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	acidoLinoleico = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	acidoLinolenico = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	altriPolins = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	colesterolo = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	fibreAnim = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	alcool = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	ferro = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	ca = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	na = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	k = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	p = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	zn = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	vitB1 = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	vitB2 = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	vitB3 = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	vitC = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	vitB6 = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	folico = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	retinolo = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	betaCarotene = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	vitE = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	vitD = models.FloatField(default=0, validators=[MinValueValidator(0.0)])
	parteEdibile = models.FloatField(default=0, validators=[MinValueValidator(0.0)])


	def __str__(self):
		return self.nome_generico

	class Meta:
		ordering = ('nome_generico','nome_generico')	#sempre tupla di 2 elementi, anche per ordinare 1 solo campo
		#ordering = ('-nome_generico','-nome_generico') ORDINE INVERSO


class Portata(models.Model):
	nome = models.CharField(max_length=100, primary_key=True)  
	posizione = models.PositiveIntegerField(validators= [MinValueValidator(1)], blank=True, null=True)

	class Meta:
		ordering = ('posizione',)

	def __str__(self): return self.nome


class CapoArea(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)

	def __str__(self): 
		return str(self.user)


class Area(models.Model):
	nome = models.CharField(max_length=100, primary_key=True) 
	capo = models.ForeignKey(CapoArea, on_delete=models.SET_NULL, blank=True, null=True)

	class Meta:
		ordering = ('nome','nome')



	def __str__(self): 
		return self.nome





class Impianto(models.Model):
	CLASSIFICAZIONI = (
	("Classico", "Classico"),
	("Plus", "Plus"),
	("Premium", "Premium"),
	)
	nome = models.CharField(max_length=100, primary_key=True) 
	area = models.ForeignKey(Area, on_delete=models.CASCADE)
	classificazione = models.CharField(max_length=8, choices=CLASSIFICAZIONI)

	class Meta:
		ordering = ('area','nome')

	def __str__(self): 
		return self.nome

	def get_absolute_url(self):
		my_date = datetime.date.today()
		annoOggi = my_date.isocalendar()[0]
		return reverse('impianto',args=[annoOggi,self.nome])





class Chef(models.Model):
	impianto = models.ForeignKey(Impianto, on_delete=models.CASCADE)
	user = models.OneToOneField(User,on_delete=models.CASCADE, related_name="user_id")
	manager = models.BooleanField(default=False)

	def __str__(self): 
		if self.user.first_name and self.user.last_name:
			return self.user.first_name + ' ' + self.user.last_name
		else:
			return self.user.username

	def clean(self):
		try:
			manager_attuale = Chef.objects.get(impianto=self.impianto,manager=True)
		except:
			#non esiste nessun manager dell'impianto
			manager_attuale = False
		if self.manager and manager_attuale:
			raise ValidationError("L'impianto '" + self.impianto.nome + "' possiede già un manager: "  +manager_attuale.user.first_name + " "+ manager_attuale.user.last_name)



class Ricetta(models.Model):
	nome = models.CharField(max_length=100, primary_key=True) 
	ingredienti = models.ManyToManyField(Ingrediente, through='Contenuto')
	tag = models.ForeignKey(Tag, on_delete=models.SET_NULL, blank=True, null=True)
	portata = models.ForeignKey(Portata, on_delete=models.SET_NULL, blank=True, null=True)
	chef = models.ForeignKey(Chef, on_delete=models.CASCADE, blank=True, null=True)
	approvata = models.BooleanField(default=False)
	foto = models.ImageField(null=True, blank=True, upload_to="ricette/") 
	special = models.BooleanField(default=False)

	class Meta:
		ordering = ('nome',)

	def __str__(self): 
		return self.nome

	def get_absolute_url(self):
		return reverse('app:pivot',args=[self.nome, ])

	#cancello anche l'eventuale foto dalla cartella media
	def delete(self, using=None, keep_parents=False):
		if self.foto:
			self.foto.storage.delete(self.foto.name)
		super().delete()


class Contenuto(models.Model):
	ingrediente = models.ForeignKey(Ingrediente, on_delete=models.CASCADE)
	ricetta = models.ForeignKey(Ricetta, on_delete=models.CASCADE)
	quantita = models.FloatField(validators=[MinValueValidator(1.0)])

	class Meta:
		unique_together = ('ingrediente', 'ricetta',)


	def __str__(self):
		return str(self.ricetta) + ' | ' +  str(self.ingrediente) + ' | ' +  str(self.quantita)



def current_year():
	return datetime.date.today().year


def max_value_current_year(value):
	return MaxValueValidator(current_year())(value)




class MenuSettimana(models.Model):
	GIORNI = ( ("Lunedi", "Lunedi"), ("Martedi", "Martedi"), ("Mercoledi", "Mercoledi"), ("Giovedi", "Giovedi"),
		("Venerdi", "Venerdi"),	)
	impianto = models.ForeignKey(Impianto, on_delete=models.CASCADE)
	anno = models.PositiveIntegerField(default=current_year(), validators=[MinValueValidator(1984), max_value_current_year])
	settimana = models.CharField(max_length=12, choices=((str(x), "Settimana "+str(x)) for x in range(1,53)))
	giorno = models.CharField(max_length=9, choices=GIORNI)
	ricette = models.ManyToManyField(Ricetta, blank=True)
	creatore = models.ForeignKey(User, on_delete=models.SET_NULL,related_name="creatore", blank=True, null=True)
	creazione = models.DateTimeField(default=timezone.now, editable=False)
	approvatore = models.ForeignKey(User, on_delete=models.SET_NULL, limit_choices_to={'is_staff': True}, blank=True,
	 									null=True, related_name='approvatore')

	class Meta:
		unique_together = ('anno','impianto', 'giorno', 'settimana',)
		ordering = ('impianto',"anno",'settimana','giorno')
	
	def __str__(self): 
		return str(self.impianto) + ": "+ str(self.giorno) + ' della settimana ' + str(self.settimana)



class HistoryMenu(models.Model):
	version = models.IntegerField(editable=False)
	menu = models.ForeignKey(MenuSettimana, on_delete=models.CASCADE)
	istante = models.DateTimeField(default=timezone.now, editable=False)
	text = models.TextField()
	user = models.ForeignKey(User, on_delete=models.CASCADE)

	class Meta:
		unique_together = ('version','menu',)
		unique_together = ('menu','text','user',)


	def save(self, *args, **kwargs):
		''' On save, update timestamps '''
		current_version = HistoryMenu.objects.filter(menu=self.menu).order_by('-version')[:1]
		self.version = current_version[0].version + 1 if current_version else 1
		return super(HistoryMenu, self).save(*args, **kwargs)

	def __str__(self): 
		return str(self.menu) + " | versione "+ str(self.version)




class Fornitore(models.Model):
	nome = models.CharField(max_length=250, primary_key=True) 

	class Meta:
		ordering = ('nome',)

	def __str__(self): 
		return str(self.nome)


class IngredienteImpianto(models.Model):
	ingrediente = models.ForeignKey(Ingrediente, on_delete=models.CASCADE)
	impianto = models.ForeignKey(Impianto, on_delete=models.CASCADE)
	listino = models.FloatField(validators=[MinValueValidator(0.0)])
	fornitore = models.ForeignKey(Fornitore, on_delete=models.SET_NULL, blank=True, null=True)


	class Meta:
		unique_together = ('ingrediente','impianto',)
		ordering = ('ingrediente__nome_generico',)

	def __str__(self): 
		return str(self.ingrediente) + ' | ' + str(self.impianto) + ' | ' +   str(self.listino) +   "€"





##################################################################################
