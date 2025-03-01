from django.shortcuts import render, redirect
from django.urls import reverse

from .models import Tag, Ricetta, Ingrediente, Portata, Contenuto, Allergene, Impianto ,Chef, MenuSettimana, IngredienteImpianto, Area, User, Fornitore, HistoryMenu, CapoArea
from django.contrib import messages
from django.db import connection, IntegrityError

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout, get_user_model
from .forms import UserLoginForm
from django.contrib.auth.decorators import login_required
import os
import datetime
from datetime import date,timedelta
from django.http import HttpResponseRedirect,HttpResponse #per redirect su stessa pagina

from django.core.paginator import Paginator

#pdf
from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.views import View

from django.db.models import Q 	#fare query con OR condition

import csv
import xlwt	#pip install xlwt
import xlrd #pip install xlrd
from io import StringIO



@login_required(login_url='/login/')
def index(request):
	annoCorrente = datetime.date.today().year
	daApprovare = 0

	impiantiTab = getImpiantiTab(request)

	if request.user.is_staff:	
		daApprovare = Ricetta.objects.filter(approvata=False).count()

		if request.method == "POST" and 'scarica' in request.POST:
			wb,response = creaFileExcel("upload ricette")

			#SHEET PRINCIPALE
			columns= ['Nome ricetta','Portata','Tag','Ingrediente','Quantità','Chef']
			rows = []
			creaSheetExcel(wb,'upload ricette',columns,rows)
			
			#SHEET INGREDIENTI
			columns= ['Ingredienti disponibili']
			rows = Ingrediente.objects.filter().values_list("nome_generico")
			creaSheetExcel(wb,'ingredienti disponibili',columns,rows)

			#SHEET PORTATE
			columns= ['portate disponibili']
			rows = Portata.objects.filter().values_list("nome")
			creaSheetExcel(wb,'portate disponibili',columns,rows)

			#SHEET TAGS
			columns= ['tags disponibili']
			rows = Tag.objects.filter().values_list("nome")
			creaSheetExcel(wb,'tags disponibili',columns,rows)

			#SHEET CHEFS
			columns= ['username']
			rows = Chef.objects.filter().values_list("user__username",flat=True)
			creaSheetExcel(wb,'chefs disponibili',columns,rows)

			wb.save(response)
			return response



		if request.method == "POST" and 'upload' in request.POST:
			if request.FILES.get('file'):
				data = request.FILES.get('file')
			else:
				return redirect('index')
			book = xlrd.open_workbook(data.name, file_contents=data.read())
			sheet = book.sheets()[0]
			nomi = sheet.col_values(0,1)
			portate = sheet.col_values(1,1)
			tags = sheet.col_values(2, 1)
			ingredienti = sheet.col_values(3, 1)
			quantita = sheet.col_values(4, 1)
			chefs = sheet.col_values(5, 1)

			caricate = 0
			for nome,portata,tag,ing,q,chef in zip(nomi,portate,tags,ingredienti,quantita,chefs):
				if nome:
					ricetta, created = Ricetta.objects.get_or_create(nome=nome.lower())
					if created: #prima riga della ricetta
						try:
							ricetta.nome = nome.lower()
							ricetta.save()
							caricate+=1
						except:
							pass
				else:
					continue

				if portata and (ricetta.portata == None):
					try:
						ricetta.portata = Portata.objects.get(nome__iexact=portata)
						ricetta.save()
					except Portata.DoesNotExist:
						pass

				if tag and (ricetta.tag == None):
					try:
						ricetta.tag = Tag.objects.get(nome__iexact=tag)
						ricetta.save()
					except Tag.DoesNotExist:
						pass

				if chef and (ricetta.chef == None):
					try:
						ricetta.chef = Chef.objects.get(user__username__iexact=chef)
						ricetta.save()
					except Chef.DoesNotExist:
						pass

				#sto aggiungendo un ingrediente
				try:
					if q and (int(q) <= 500 and int(q) > 0):
						try:
							try:
								ingObj = Ingrediente.objects.get(nome_generico__iexact = ing.lower())
							except Ingrediente.DoesNotExist:
								ingObj = Ingrediente.objects.filter(Q(nome_generico__icontains = ing.lower()))[0]
							if ingObj:
								try:
									c = Contenuto.objects.get(ingrediente=ingObj,ricetta=ricetta)
									c.quantita=int(q)
								except Contenuto.DoesNotExist:
									c = Contenuto(ingrediente=ingObj, ricetta=ricetta, quantita=int(q))
								c.save()
						except:
							pass
				except ValueError:
					pass
					


			messages.success(request, str(caricate) +' ricette caricate con successo nel sistema')
			return redirect('index')


	return render(request, 'app/index.html', {'annoCorrente':annoCorrente,'impiantiTab':impiantiTab,'daApprovare':daApprovare})
	


def login_view(request):
	next = request.GET.get('next')
	form = UserLoginForm(request.POST or None)
	if form.is_valid():
		username = form.cleaned_data.get('username')
		password = form.cleaned_data.get('password')
		
		u = User.objects.get(username__iexact=username)
		user = authenticate(username=u, password= password)
		if user is not None:
			login(request, user)
			if next:
				return redirect(next)
			return redirect('/')
	return render(request, "login.html", {'form':form})




@login_required(login_url='/login/')
def logout_view(request):
	logout(request)
	return redirect('/')


@login_required(login_url='/login/')
def visualizzaIngredienti(request,filtro=""):
	if not request.user.is_staff:
		messages.error(request, 'Non hai accesso a questa pagina')
		return redirect('index')



	if request.method == "POST" and 'conferma-ingrediente' in request.POST:
		nome_generico = request.POST.get('nome_generico')
		try:
			obj = Ingrediente.objects.get(nome_generico__iexact=nome_generico)
			messages.error(request, 'Ingrediente già esistente nel sistema')
			return redirect('ingredienti')
		except Ingrediente.DoesNotExist:
			obj = Ingrediente()
			kcal = float(request.POST.get('kcal'))
			obj.nome_generico = nome_generico.lower()
			obj.nome_specifico = request.POST.get('nome_specifico').lower()
			obj.energiaKcal = kcal
			obj.energiaKj = round(kcal * 4.184, 2)
			obj.acqua = float(request.POST.get('acqua'))
			obj.acqua = float(request.POST.get('acqua'))
			obj.protAnim = float(request.POST.get('animali'))
			obj.protVeg = float(request.POST.get('vegetali'))
			obj.protTot = float(request.POST.get('animali')) + float(request.POST.get('vegetali'))
			obj.amido = float(request.POST.get('amido'))
			obj.glucidiSolub = float(request.POST.get('solubili'))
			obj.saturi = float(request.POST.get('saturi'))
			obj.monoins = float(request.POST.get('monoinsaturi'))
			obj.polins = float(request.POST.get('polinsaturi'))
			obj.altriPolins = float(request.POST.get('altri_polinsaturi'))
			obj.glucidiTot = float(request.POST.get('amido')) + float(request.POST.get('solubili'))
			obj.lipidiTot = float(request.POST.get('saturi')) + float(request.POST.get('monoinsaturi')) + float(request.POST.get('polinsaturi')) + float(request.POST.get('altri_polinsaturi'))
			obj.listino = float(request.POST.get('listino'))
			obj.save()

			for imp in Impianto.objects.all():
				obj2 = IngredienteImpianto()
				obj2.impianto = imp
				obj2.ingrediente = obj
				obj2.listino = float(request.POST.get('listino'))
				obj2.save()

			messages.success(request, 'Ingrediente creato con successo')
			return redirect('ingredienti')



	if request.method == "POST" and 'elimina' in request.POST:
		nome = request.POST.get('elimina')
		obj = Ingrediente.objects.get(nome_generico__iexact= nome)
		obj.delete()
		messages.success(request, 'Ingrediente eliminato con successo')
		return redirect('ingredienti')


	if request.method == "POST" and 'cerca' in request.POST:
		filtro = request.POST.get('filtro')
		if filtro == "":
			return redirect('ingredienti')
		else:	
			return redirect(reverse('ingredienti-filtro', kwargs = {'filtro':filtro}))


	if filtro:
		ingredienti = Ingrediente.objects.filter(nome_generico__icontains=filtro)
	else:
		ingredienti = Ingrediente.objects.all()
	count = ingredienti.count()

	paginator = Paginator(ingredienti, 50) 
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	nums = "a" * page_obj.paginator.num_pages


	if request.method == "POST" and 'salva' in request.POST:
		i = 0
		for obj in page_obj:
			cambioPrezzo,cambioFornitore = False, False
			nuovoPrezzo = request.POST.get(obj.nome_generico+"-listino")
			if nuovoPrezzo != None:
				nuovoPrezzo = float(nuovoPrezzo)
				
				if nuovoPrezzo != obj.listino: 
					obj.listino = nuovoPrezzo
					obj.save()
					cambioPrezzo = True
					i+=1
		
		messages.success(request, str(i) + " ingredienti aggiornati con successo"  )


		return redirect('ingredienti')


	return render(request, 'app/visualizza_ingredienti.html', {'page_obj':page_obj, 'nums':nums,'count':count,'filtro':filtro})



@login_required(login_url='/login/')
def listinoImpianto(request, pk, filtro=""):
	try:	#controllo se l'impianto esiste o se qualcuno ha fatto il furbo
		impianto = Impianto.objects.get(nome=pk)
	except Impianto.DoesNotExist:
		messages.error(request, ('Impianto inesistente'))
		return redirect('index')
	if not request.user.is_staff:
		messages.error(request, 'Non hai accesso a questa pagina')
		return redirect('index')
	

	annoCorrente = datetime.date.today().year

	if filtro:
		ingredientiImpianto = IngredienteImpianto.objects.filter(impianto=impianto, ingrediente__nome_generico__contains=filtro)
	else:
		ingredientiImpianto = IngredienteImpianto.objects.filter(impianto=impianto)

	fornitori = Fornitore.objects.all()

	paginator = Paginator(ingredientiImpianto, 50) 
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	nums = "a" * page_obj.paginator.num_pages

	

	if request.method == "POST" and 'cerca' in request.POST:
		filtro = request.POST.get('filtro')
		if filtro == "":
			return redirect(reverse('listinoimpianto', kwargs = {'pk' : impianto.nome}))
		else:	
			return redirect(reverse('listinoimpianto-filtro', kwargs = {'pk' : impianto.nome,'filtro':filtro}))
	

	if request.method == "POST" and 'salva' in request.POST:
		i = 0
		for obj in page_obj:
			cambioPrezzo,cambioFornitore = False, False
			ing = obj.ingrediente
			
			fornitoreStr = request.POST.get(ing.nome_generico+"-fornitore")
			if fornitoreStr:
				fornitoreObj = Fornitore.objects.get(nome__iexact=fornitoreStr)
			else:
				fornitoreObj = None
			if fornitoreObj != obj.fornitore:
					IngredienteImpianto.objects.filter(ingrediente=ing,impianto=impianto).update(fornitore=fornitoreObj)
					cambioFornitore = True

			nuovoPrezzo = request.POST.get(ing.nome_generico)
			if nuovoPrezzo != None:
				nuovoPrezzo = float(nuovoPrezzo)
				if nuovoPrezzo != obj.listino: 
					IngredienteImpianto.objects.filter(ingrediente=ing,impianto=impianto).update(listino=nuovoPrezzo)
					cambioPrezzo = True

			if cambioFornitore or cambioPrezzo:
				i+=1
		
		messages.success(request, str(i) + " ingredienti aggiornati con successo"  )


		return redirect(reverse('listinoimpianto', kwargs = {'pk' : impianto.nome}))	


	if request.method == "POST" and 'scarica' in request.POST:
		nome_file = "Listino prezzi "+ impianto.nome
		wb,response = creaFileExcel(nome_file)

		#SHEET PRINCIPALE
		columns = ['Ingrediente', 'Listino','Fornitore']
		rows = IngredienteImpianto.objects.filter(impianto=impianto).values_list('ingrediente', 'listino','fornitore')
		creaSheetExcel(wb,nome_file,columns,rows)

		#SHEET FORNITORI
		columns = ["fornitori disponibili"]
		rows = Fornitore.objects.filter().values_list('nome')
		creaSheetExcel(wb,'fornitori disponibili',columns,rows)

		wb.save(response)
		return response

	
	if request.method == "POST" and 'upload' in request.POST:
		if request.FILES:
			data = request.FILES.get('file')
		else:
			return redirect(reverse('listinoimpianto', kwargs = {'pk' : impianto.nome}))
		book = xlrd.open_workbook(data.name, file_contents=data.read())
		sheet = book.sheets()[0]
		nomi = sheet.col_values(0,1)
		listini = sheet.col_values(1,1)
		fornitori = sheet.col_values(2, 1)
		i = 0
		for nome,listino,fornitore in zip(nomi,listini,fornitori):
			cambioPrezzo,cambioFornitore = False, False
			try:
				ing = Ingrediente.objects.get(nome_generico__iexact=nome )
				obj = IngredienteImpianto.objects.get(impianto=impianto, ingrediente=ing)
				if obj.listino != listino:
					obj.listino = listino
					obj.save()	
					cambioPrezzo = True
				
				if fornitore:
					fornitoreObj = Fornitore.objects.filter(Q(nome__iexact=fornitore) | Q(nome__icontains=fornitore))[0] 
				else:
					fornitoreObj = None
				if obj.fornitore != fornitoreObj:
					obj.fornitore = fornitoreObj 
					obj.save()
					cambioFornitore = True

				if cambioPrezzo or cambioFornitore:
					i+=1
			except:
				pass
		
		messages.success(request,str(i)+ " modifiche effettuate con successo" )

		return redirect(reverse('listinoimpianto', kwargs = {'pk':impianto.nome}))
	


	return render(request, 'app/listino_impianto.html', {'impianto':impianto,'page_obj':page_obj,'annoCorrente':annoCorrente,'fornitori':fornitori,'nums':nums,'filtro':filtro})


@login_required(login_url='/login/')
def visualizzaFornitori(request):
	if not request.user.is_staff:
		messages.error(request, 'Non hai accesso a questa pagina')
		return redirect('index')
		
	fornitori = Fornitore.objects.all().order_by('nome')
	count = fornitori.count()

	paginator = Paginator(fornitori, 50) 
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	nums = "a" * page_obj.paginator.num_pages

	if request.method == "POST" and 'conferma-fornitore' in request.POST:
		nuovoFornitore(request)
		return redirect('fornitori')

	if request.method == "POST" and 'elimina' in request.POST:
		eliminaFornitore(request)   
		return redirect('fornitori')

	return render(request, 'app/visualizza_fornitori.html', {'count':count,'page_obj':page_obj,'nums':nums})



@login_required(login_url='/login/')
def visualizzaUtenti(request):
	if not request.user.is_staff:
		messages.error(request, 'Non hai accesso a questa pagina')
		return redirect('index')

	utenti = User.objects.all().order_by('username')
	impianti = Impianto.objects.filter().order_by('nome')
	count = utenti.count()
	aree = Area.objects.all()

	paginator = Paginator(utenti, 50) 
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	nums = "a" * page_obj.paginator.num_pages

	if request.method == "POST" and 'conferma-chef' in request.POST:
		nuovoChef(request)
		return redirect('utenti')


	if request.method == "POST" and 'conferma-direzionale' in request.POST:
		nuovoUtenteDirezionale(request)
		return redirect('utenti')


	if request.method == "POST" and 'conferma-capoarea' in request.POST:
		nuovoCapoArea(request)
		return redirect('utenti')

	if request.method == "POST" and 'elimina' in request.POST:
		eliminaUtente(request)   
		return redirect('utenti')


	if request.method == "POST" and 'cambia' in request.POST:
		cambiaPassword(request)
		return redirect('utenti')

		

	return render(request, 'app/visualizza_utenti.html', {'impianti':impianti,'aree':aree,'count':count,'page_obj':page_obj,'nums':nums})


@login_required(login_url='/login/')
def visualizzaUtentiChefs(request):
	if not request.user.is_staff:
		messages.error(request, 'Non hai accesso a questa pagina')
		return redirect('index')

	aree = Area.objects.all()
	impianti = Impianto.objects.all().order_by('nome')

	chefs = Chef.objects.filter().values_list('user_id')
	utenti = User.objects.filter( Q(id__in=chefs))
	count = utenti.count()

	paginator = Paginator(utenti, 50) 
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	nums = "a" * page_obj.paginator.num_pages

	if request.method == "POST" and 'conferma-chef' in request.POST:
		nuovoChef(request)
		return redirect('utenti-chefs')


	if request.method == "POST" and 'conferma-direzionale' in request.POST:
		nuovoUtenteDirezionale(request)
		return redirect('utenti-chefs')

	if request.method == "POST" and 'conferma-capoarea' in request.POST:
		nuovoCapoArea(request)
		return redirect('utenti-chefs')


	if request.method == "POST" and 'elimina' in request.POST:
		eliminaUtente(request)   
		return redirect('utenti-chefs')


	if request.method == "POST" and 'cambia' in request.POST:
		cambiaPassword(request)
		return redirect('utenti-chefs')


	return render(request, 'app/visualizza_utenti_chefs.html', {'aree':aree,'impianti':impianti,'count':count,'page_obj':page_obj,'nums':nums})


@login_required(login_url='/login/')
def visualizzaUtentiChefsImpianto(request,pk):
	if not request.user.is_staff:
		messages.error(request, 'Non hai accesso a questa pagina')
		return redirect('index')
	try:
		impianto = Impianto.objects.get(nome=pk)
	except Impianto.DoesNotExist:
		messages.error(request, ('Impianto inesistente'))
		return redirect('index')

	impianti = Impianto.objects.filter().order_by('nome')
	aree = Area.objects.all()

	chefs = Chef.objects.filter(impianto=impianto).values_list('user_id')
	utenti = User.objects.filter( Q(id__in=chefs))
	count = utenti.count()

	paginator = Paginator(utenti, 50) 
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	nums = "a" * page_obj.paginator.num_pages

	if request.method == "POST" and 'conferma-chef' in request.POST:
		nuovoChef(request)
		return redirect(reverse('utenti-chefs-impianto', kwargs = {'pk' : impianto.nome}))


	if request.method == "POST" and 'conferma-direzionale' in request.POST:
		nuovoUtenteDirezionale(request)
		return redirect(reverse('utenti-chefs-impianto', kwargs = {'pk' : impianto.nome}))


	if request.method == "POST" and 'conferma-capoarea' in request.POST:
		nuovoCapoArea(request)
		return redirect(reverse('utenti-chefs-impianto', kwargs = {'pk' : impianto.nome}))


	if request.method == "POST" and 'elimina' in request.POST:
		eliminaUtente(request)   
		return redirect(reverse('utenti-chefs-impianto', kwargs = {'pk' : impianto.nome}))


	if request.method == "POST" and 'cambia' in request.POST:
		cambiaPassword(request)
		return redirect(reverse('utenti-chefs-impianto', kwargs = {'pk' : impianto.nome}))



	return render(request, 'app/visualizza_utenti_chefs_impianto.html', {'aree':aree,'impianto':impianto,'impianti':impianti,'count':count,'page_obj':page_obj,'nums':nums})



@login_required(login_url='/login/')
def visualizzaUtentiDirezionali(request):
	if not request.user.is_staff:
		messages.error(request, 'Non hai accesso a questa pagina')
		return redirect('index')

	admins = User.objects.filter(is_staff=True).order_by('username')
	impianti = Impianto.objects.filter().order_by('nome')
	count = admins.count()
	aree = Area.objects.all()

	paginator = Paginator(admins, 50) 
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	nums = "a" * page_obj.paginator.num_pages

	if request.method == "POST" and 'conferma-chef' in request.POST:
		nuovoChef(request)
		return redirect('utenti-direzionali')


	if request.method == "POST" and 'conferma-direzionale' in request.POST:
		nuovoUtenteDirezionale(request)
		return redirect('utenti-direzionali')

	if request.method == "POST" and 'conferma-capoarea' in request.POST:
		nuovoCapoArea(request)
		return redirect('utenti-direzionali')


	if request.method == "POST" and 'elimina' in request.POST:
		eliminaUtente(request)   
		return redirect('utenti-direzionali')



	if request.method == "POST" and 'cambia' in request.POST:
		cambiaPassword(request)
		return redirect('utenti-direzionali')


	return render(request, 'app/visualizza_utenti_direzionali.html', {'aree':aree,'impianti':impianti,'count':count,'page_obj':page_obj,'nums':nums})



@login_required(login_url='/login/')
def visualizzaUtentiCapoarea(request):
	if not request.user.is_staff:
		messages.error(request, 'Non hai accesso a questa pagina')
		return redirect('index')
	aree = Area.objects.all()
	impianti = Impianto.objects.all().order_by('nome')
	
	capoarea = CapoArea.objects.filter().values_list('user_id')
	utenti = User.objects.filter( Q(id__in=capoarea))
	count = utenti.count()

	paginator = Paginator(utenti, 50) 
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	nums = "a" * page_obj.paginator.num_pages


	if request.method == "POST" and 'conferma-chef' in request.POST:
		nuovoChef(request, 'utenti-capoarea')
		return redirect('utenti-capoarea')

	if request.method == "POST" and 'conferma-direzionale' in request.POST:
		nuovoUtenteDirezionale(request)
		return redirect('utenti-capoarea')

	if request.method == "POST" and 'conferma-capoarea' in request.POST:
		nuovoCapoArea(request)
		return redirect('utenti-capoarea')

	if request.method == "POST" and 'elimina' in request.POST:
		eliminaUtente(request)   
		return redirect('utenti-capoarea')


	if request.method == "POST" and 'cambia' in request.POST:
		cambiaPassword(request)
		return redirect('utenti-capoarea')


	return render(request, 'app/visualizza_utenti_capoarea.html', {'page_obj':page_obj,'nums':nums,'count':count,'aree':aree,'impianti':impianti})




@login_required(login_url='/login/')
def approvaRicetta(request, filtro=""):
	if request.user.is_staff:
		if filtro:
			ricette = Ricetta.objects.filter( Q(approvata=False) &  ( Q(nome__contains=filtro)  | Q(chef__impianto__nome__contains=filtro) | Q(chef__user__username__contains=filtro) | Q(tag__nome__contains=filtro) | Q(portata__nome__contains=filtro) )  ) 
		else:
			ricette = Ricetta.objects.filter(approvata=False)
		count = ricette.count()

		paginator = Paginator(ricette, 50) 
		page_number = request.GET.get('page')
		page_obj = paginator.get_page(page_number)
		nums = "a" * page_obj.paginator.num_pages
		
		if request.method == "POST" and 'elimina' in request.POST:
			eliminaRicetta(request)
			return redirect('approvaricetta')


		if request.method == "POST" and 'cerca' in request.POST:
			filtro = request.POST.get('filtro')
			if filtro == "":
				return redirect(reverse('approvaricetta'))
			else:	
				return redirect(reverse('approvaricetta-filtro', kwargs = {'filtro':filtro}))


		return render(request, 'app/approva_ricetta.html', {'page_obj':page_obj,'nums':nums,'count':count,'filtro':filtro})
		

	else:
		messages.error(request, 'Non hai accesso a questa pagina')
		return redirect('index')




@login_required(login_url='/login/')
def visualizzaIngrediente(request,nome):
	if not request.user.is_staff:
		messages.error(request, 'Non hai accesso a questa pagina')
		return redirect('index')

	try:
		nome = nome.lower()
		ing = Ingrediente.objects.get(nome_generico=nome)
	except Ingrediente.DoesNotExist:
		messages.error(request, ('Ingrediente inesistente'))
		return redirect(reverse('visualizzaingredienti'))

	ingredienti = Ingrediente.objects.values()
	campi = dict()
	for diz in ingredienti:
		for campo,value in diz.items():
			if (campo=='nome_generico') and (value == ing.nome_generico):
				campi = diz


	return render(request, 'app/visualizza_ingrediente.html', {'ing':ing,'campi':campi})



@login_required(login_url='/login/')
def gestioneImpiantiAree(request):
	if not request.user.is_staff:
		messages.error(request, 'Non hai accesso a questa pagina')
		return redirect('index')

	aree = Area.objects.all()
	totAree = aree.count()
	totImpianti = Impianto.objects.all().count()
	my_date = datetime.date.today()
	annoOggi = my_date.isocalendar()[0]
	classificazioni = ['Classico','Plus','Premium']

	areaImpianti = dict()
	for area in aree:
		areaImpianti[area] = Impianto.objects.filter(area=area)

	diz = dict()
	for area in aree:
		daEscludere = Area.objects.filter().exclude( Q(capo__isnull=True) | Q(capo=area.capo)).values_list('capo',flat=True)

		diz[area] = CapoArea.objects.filter().exclude(id__in=daEscludere)



	if request.method == "POST" and 'conferma-impianto' in request.POST:
		nome = request.POST.get('nome').lower()
	
		try:
			Impianto.objects.get(nome__iexact = nome)
			messages.error(request, ('Impianto già esistente'))
			return HttpResponseRedirect(request.path_info)
		except Impianto.DoesNotExist:
			pass
			
		#l'impianto è nuovo: ricavo l'area inserita
		area = Area.objects.get(nome=request.POST.get('area'))  
		classificazione = request.POST.get('classificazione')
		#creo l'impianto
		nuova = Impianto()
		nuova.nome = nome
		nuova.area= area
		nuova.classificazione = classificazione
		nuova.save()
		#inizializzo i prezzi degli ingredienti
		impianto = Impianto.objects.get(nome__iexact=nome)
		for ing in Ingrediente.objects.all():
			nuova2 = IngredienteImpianto()
			nuova2.ingrediente = ing
			nuova2.impianto = impianto
			nuova2.listino = round(media(IngredienteImpianto.objects.filter(ingrediente=ing).values_list('listino',flat=True)), 2)
			nuova2.save()

		messages.success(request, ('Impianto creato con successo!'))
		return redirect(reverse('impianto', kwargs = {'pk' : nome,'year':annoOggi}))


	if request.method == "POST" and 'conferma-area' in request.POST:
		nomeInput = request.POST.get("nome")
		try:
			Area.objects.get(nome__iexact=nomeInput)
			messages.error(request, ('Area già esistente'))
			return HttpResponseRedirect(request.path_info)
		except Area.DoesNotExist:
			pass
		#l'area non esiste
		obj = Area(nome=nomeInput.lower())
		obj.save()
		messages.success(request, ("Area '"+ obj.nome + "' creata con successo"))
		return redirect('gestione-impianti-aree')


	if request.method == "POST" and 'elimina' in request.POST:
		areaStr = request.POST.get('elimina')
		try:
			a = Area.objects.get(nome__iexact = areaStr)
			a.delete()
			messages.success(request, "area '" +areaStr + "' eliminata con successo")
		except Area.DoesNotExist:
			messages.error(request, "Errore, area inesistente")
		return redirect('gestione-impianti-aree')


	if request.method == "POST" and 'aggiorna' in request.POST:
		areaStr = request.POST.get("aggiorna")
		area = Area.objects.get(nome__iexact=areaStr)

		if request.POST.get(area.nome) == "":
			area.capo = None
			area.save()

		else:
			nuovo = User.objects.get(username = request.POST.get(area.nome) )
			capoarea = CapoArea.objects.get(user=nuovo)
			area.capo = capoarea
			area.save()
	
		return redirect('gestione-impianti-aree')


	return render(request, 'app/gestione_impianti_aree.html', {'aree':aree,'totAree':totAree,'diz':diz,'areaImpianti':areaImpianti,'totImpianti':totImpianti,'classificazioni':classificazioni})



@login_required(login_url='/login/')
def nuovaRicetta(request,filtro=""):
	portate = Portata.objects.all()
	ricette = Ricetta.objects.all()

	tags = ricavaTagsDellaPortata(filtro)

	if request.user.is_staff:
			chefs = list(Chef.objects.filter(manager=True))
			chefs.append("")
	else:
		try:
			requestChef = Chef.objects.get(user = request.user) #sono uno chef..
			if requestChef.manager:	#..e sono un manager: chefs= tutti gli chef del mio impianto
				chefs = Chef.objects.filter(impianto=requestChef.impianto)
			else: #..e non sono un manager: chefs= soltanto io
				chefs = [requestChef]
		except Chef.DoesNotExist:
			pass
		try:
			area = Area.objects.get(capo__user=request.user)
			chefs = Chef.objects.filter( Q(impianto__area=area) & Q(manager=True) )
		except Area.DoesNotExist:
			pass
			

	if request.method == "POST" and 'cerca' in request.POST:
		return redirect("https://www.google.it/search?q="+ str(request.POST['nome']).lower())



	if request.method == "POST" and 'Save' in request.POST:
		nome = str(request.POST['nome']).lower()		#input utente
		try: #se già esiste nel db la ricetta con quel nome allora non lo permetto
			if Ricetta.objects.get(nome__iexact=nome): 
				messages.error(request, ('ricetta ' +nome+' già esistente nel sistema'))
				return redirect(reverse('nuovaricetta'))
		except:
			pass
		#la ricetta è nuova: procedo alla creazione
		if len(str(request.POST['chef'])) > 0 : # è stato assegnato uno chef
			chef = Chef.objects.get(user = str(request.POST['chef']))  
		else:	#non è stato assegnato nessuno chef (solo gli admin possono)
			chef = None
		t = Tag.objects.get(nome=str(request.POST['tag'])) 
		p = Portata.objects.get(nome=str(request.POST['portata']))

		nuova = Ricetta()
		nuova.nome = nome
		nuova.portata = p
		nuova.tag = t
		nuova.chef = chef
		if len(request.FILES) != 0:
			nuova.foto = request.FILES['image']
		if request.POST.get("special"):
			nuova.special = True
		nuova.save()

		messages.success(request, ('Ricetta ' +nome + ' creata con successo!'))
		messages.info(request, ('Ora puoi inserire gli ingredienti'))
		
		return redirect(reverse('pivot', kwargs = {'pk' : nome}))



	return render(request, 'app/nuova_ricetta.html', {'tags':tags, 'portate':portate,'chefs':chefs,'filtro':filtro})



@login_required(login_url='/login/')
def consultaRicette(request):
	if request.user.is_staff:
			ricette = Ricetta.objects.all()
			impianti = Impianto.objects.all()
	else:
		try:
			io = Chef.objects.get(user=request.user)
			#sono uno chef:
			if io.impianto.classificazione == "Classico":
				ricette = Ricetta.objects.filter( (Q(chef__impianto=io.impianto )  | Q(approvata=True)  ) &  Q(special=False) ) 
			else:
				ricette = Ricetta.objects.filter( Q(chef__impianto=io.impianto ) | Q(approvata=True))
		except Chef.DoesNotExist:
			area = Area.objects.get(capo__user=request.user)
			classificazioni = set(Impianto.objects.filter(area=area).values_list('classificazione',flat=True))
			if "Premium" or "Plus" in classificazioni:
				ricette = Ricetta.objects.filter( Q(chef__impianto__area = area) | Q(approvata=True))
			else:
				ricette = Ricetta.objects.filter( (Q(chef__impianto__area=area )  | Q(approvata=True)  ) &  Q(special=False) ) 
	

		impianti = []
		impiantiFiltro = set(ricette.values_list('chef__impianto',flat=True))
		for imp in impiantiFiltro:
			if imp != None:
				impianti.append(Impianto.objects.get(nome__iexact=imp))


	tags = Tag.objects.all()
	portate = Portata.objects.all()

	if request.method == "POST" and 'cerca' in request.POST:
		nome = str(request.POST.get('ricerca_per_nome')).lower()

		ricettaCercata = Ricetta.objects.filter( Q(nome__icontains=nome) & Q(nome__in=ricette))
		count = ricettaCercata.count()

		if count == 0:
			messages.error(request, ('Errore: Nessuna ricetta trovata con la parola chiave "'+ nome + '"' ))
			return redirect(reverse('consultaricette'))
		if count == 1:
			return redirect(reverse('pivot', kwargs = {'pk' : ricettaCercata[0].nome }))
		if count > 1:
			return render(request, 'app/consulta_ricette.html', {'ricette':ricette,'portate':portate,'tags':tags,'ricetteFiltro':ricettaCercata,'impianti':impianti,'count':count})
		
	

	if request.method == "POST" and 'filtro' in request.POST:
		tagsFiltro = set(ricette.values_list('tag',flat=True))
		portateFiltro = set(ricette.values_list('portata',flat=True))

		if request.POST.get('tag') != "":
			tag = [Tag.objects.get(nome=request.POST.get('tag'))]
		else:
			tag = tagsFiltro

		if request.POST.get('portata') != "":
			portata = [Portata.objects.get(nome=request.POST.get('portata'))]
		else:
			portata = portateFiltro


		if request.POST.get('impianto') != "":
			impianto = [Impianto.objects.get(nome=request.POST.get('impianto'))]
			tuttiImpianti = False
		else:
			impianto = impianti
			tuttiImpianti = True
		
		if tuttiImpianti:
			ricetteFiltro = Ricetta.objects.filter( Q(tag__in=tag) & Q(portata__in=portata) & Q(nome__in=ricette) )
		else:
			ricetteFiltro = Ricetta.objects.filter( Q(tag__in=tag) & Q(portata__in=portata) & Q(nome__in=ricette) & (Q(chef__impianto__in=impianto)) )

		count = ricetteFiltro.count()
		return render(request, 'app/consulta_ricette.html', {'ricette':ricette,'portate':portate,'tags':tags,'ricetteFiltro':ricetteFiltro,'impianti':impianti,'count':count})
	
	

	return render(request, 'app/consulta_ricette.html', {'ricette':ricette,'portate':portate,'tags':tags,'impianti':impianti})



@login_required(login_url='/login/')
def pivot(request,pk,imp=""):
	try:
		ricetta = Ricetta.objects.get(nome__iexact=pk)
	except Ricetta.DoesNotExist:
		messages.error(request, ('Ricetta non trovata'))
		return redirect('index')
	#qui la ricetta esiste
	ingredientes = Ingrediente.objects.all()
	ingredienti = ingredientiRicettaConQuantita(ricetta) #dizionario

	if request.user.is_staff:
		imps = list(Impianto.objects.filter().values_list('nome',flat=True).order_by('nome'))
		impianti = None
	else:
		try: 
			impianti = [Chef.objects.get(user=request.user).impianto]
		except Chef.DoesNotExist:
			try: 
				capo = CapoArea.objects.get(user= request.user)
				impianti = Impianto.objects.filter(area__capo=capo).values_list('nome',flat=True)
			except:
				pass
		imps = list(Impianto.objects.filter(nome__in=impianti).values_list('nome',flat=True).order_by('nome'))
	imps.insert(0,'tutti gli impianti')
	if imp:
		if imp not in imps: #impianto non valido
			return redirect(reverse('pivot', kwargs = {'pk' : ricetta.nome}))
		impianti = [Impianto.objects.get(nome__iexact=imp)]

	bottoneModifica = False
	if request.user.is_staff:
			bottoneModifica = True
	try: #sono uno chef
		chef = Chef.objects.get(user = request.user)
		if chef.manager and ricetta.approvata==False:
			bottoneModifica = True
		else:
			if (type(ricetta.chef) != type(None)) and (ricetta.chef == chef) and (ricetta.approvata==False):
				bottoneModifica = True
	except Chef.DoesNotExist: #sono un capoarea
		try:
			area = Area.objects.get(capo= CapoArea.objects.get(user=request.user))
			if (type(ricetta.chef) != type(None)) and (area == ricetta.chef.impianto.area) and (ricetta.approvata==False):
				bottoneModifica = True
		except:
			pass

	if request.method == "POST" and 'elimina' in request.POST:
		valori = request.POST.get('elimina').split("|")
		ing = Ingrediente.objects.get(nome_generico__iexact= valori[0] )
		ricetta = Ricetta.objects.get(nome__iexact =valori[1])
		c = Contenuto.objects.get(ricetta=ricetta,ingrediente=ing)
		c.delete()
		messages.success(request, ('Ingrediente eliminato con successo dalla ricetta'))
		return redirect(reverse('pivot', kwargs = {'pk' : nome}))


	if request.method == "POST" and 'approva' in request.POST:
		if not(request.user.is_staff): #controllo per robustezza (il bottone tanto lo vedono sono gli admin)
				messages.error(request, ('Non puoi approvare la ricetta'))
		ricetta.approvata = True
		ricetta.save()
		return redirect(reverse('pivot', kwargs = {'pk' : nome}))


	if request.method == "POST" and 'aggiungi' in request.POST:
		try:
			if ricetta.chef.user:	#controllo se esiste uno chef proprietario
				if not bottoneModifica:
					messages.error(request, ('Non puoi modificare la ricetta'))
					return redirect(reverse('pivot', kwargs = {'pk' : nome}))
		except: #non cè un creatore. Controllo se sono uno staffer
			if not(request.user.is_staff):
				messages.error(request, ('Non puoi modificare la ricetta'))
				return redirect(reverse('pivot', kwargs = {'pk' : nome}))
		# ..e controllo il nuovo ingrediente..
		nome_ing = str(request.POST.get('ingre'))
		try:
			quantita = int(request.POST.get('q'))
		except ValueError: #la casella della quantità è vuota
			messages.error(request, ('Seleziona una quantità corretta'))
			return redirect(reverse('pivot', kwargs = {'pk' : nome}))

		try:
			ing = Ingrediente.objects.get(nome_generico__iexact=nome_ing)
		except Ingrediente.DoesNotExist:
			messages.error(request, ('Ingrediente non esistente nel sistema'))
			return redirect(reverse('pivot', kwargs = {'pk' : nome}))
		#..se il nuovo ingrediente esiste allora controllo se già era nella ricetta
		try:
			content = Contenuto.objects.get(ingrediente=ing,ricetta=ricetta)
			messages.warning(request, ('Errore, la ricetta contiene già '+ str(content.quantita) + ' gr di ' + nome_ing))
			return redirect(reverse('pivot', kwargs = {'pk' : nome}))
		except Contenuto.DoesNotExist:
			content = Contenuto(ingrediente=ing,ricetta=ricetta, quantita = quantita)
			content.save()
			messages.success(request, (str(quantita) + ' gr di ' +nome_ing + ' aggiunti con successo alla ricetta ' + nome+''))
		
		return redirect(reverse('pivot', kwargs = {'pk' : nome}))

	
	diz, complessivo, listaAllerg = creaTabellaPivot(ricetta,impianti)

	return render(request, 'app/pivot.html', {'ricetta':ricetta, 'diz':diz, 
												'totale':complessivo, 'allergeni':listaAllerg,
												'ingredientes':ingredientes,'bottoneModifica':bottoneModifica,'imps':imps,'imp':imp})





@login_required(login_url='/login/')
def modificaRicetta(request,pk,filtro):
	try:
		ricetta = Ricetta.objects.get(nome=pk.lower())
	except Ricetta.DoesNotExist:
		messages.error(request, ('Errore: ricetta non trovata'))
		return redirect('index')
	portate = Portata.objects.all()

	ingredienti = ingredientiRicettaConQuantita(ricetta)

	tags = ricavaTagsDellaPortata(filtro)

	possoModificare = False
	if request.user.is_staff:
			chefs = list(Chef.objects.filter(manager=True))
			if ricetta.chef and ricetta.chef not in chefs: #il proprietario è uno chef normale e lo aggiungo alla lista
				chefs.append(ricetta.chef)
			chefs.append("")
	else:
		try: #sono uno chef
			chef = Chef.objects.get(user = request.user)
			if chef.manager:
				chefs = Chef.objects.filter(impianto=chef.impianto)
				possoModificare = True
			else:
				if (type(ricetta.chef) != type(None)) and (ricetta.chef == chef) :
					chefs = [chef]
					possoModificare = True
		except Chef.DoesNotExist: #sono un capoarea
			try:
				area = Area.objects.get(capo= CapoArea.objects.get(user=request.user))
				chefs = Chef.objects.filter( Q(impianto__area =  area) & Q(manager=True)) 
				if (type(ricetta.chef) != type(None)) and (area == ricetta.chef.impianto.area):
					possoModificare = True
			except:
				pass
		

	condizioneModifica = (request.user.is_staff) or (possoModificare and ricetta.approvata==False)
	if not condizioneModifica:
		messages.error(request, ('Non puoi modificare la ricetta'))
		return redirect(reverse('pivot', kwargs = {'pk' : pk}))


	if request.method == "POST" and 'eliminaFoto' in request.POST:
		os.remove(ricetta.foto.path)
		ricetta.foto.delete(save=True)
		return redirect(reverse('pivot', kwargs = {'pk' : ricetta.nome}))

	if request.method == "POST" and 'fatto' in request.POST:
		modificato = False

		if len(str(request.POST.get('chef'))) == 0 : # non è stato assegnato uno chef
			ricetta.chef = None
		else:	
			#è stato assegnato uno chef
			chefNuovo = Chef.objects.get(user = str(request.POST['chef']))
			if ricetta.chef != chefNuovo: #lo chef è cambiato 
				modificato = True
				ricetta.chef = chefNuovo

		nuovaPortata = str(request.POST.get('portata'))
		if (ricetta.portata == None) or (ricetta.portata.nome != nuovaPortata): #se cambia la portata
			modificato = True
			try:
				ricetta.portata = Portata.objects.get(nome=nuovaPortata)
			except Portata.DoesNotExist:
				ricetta.portata = None 
			
		nuovoTag = str(request.POST.get('tag'))
		if (ricetta.tag == None) or (ricetta.tag.nome != nuovoTag): #se cambia il tag
			modificato = True
			try:
				ricetta.tag = Tag.objects.get(nome=nuovoTag)
			except Tag.DoesNotExist:
				ricetta.tag = None

		if len(request.FILES) != 0: #Se viene aggiornata l'immagine
			modificato = True
			if ricetta.foto:
				os.remove(ricetta.foto.path)
				ricetta.foto.delete(save=True)
			ricetta.foto = request.FILES['image']
			
		ricetta.save()

		#se elimina ingredienti
		for ing in ricetta.ingredienti.all():
			if request.POST.get(ing.nome_generico+"-gr"):
				c = Contenuto.objects.get(ingrediente=ing,ricetta=ricetta)
				nuovaQuantita = float(request.POST.get(ing.nome_generico+"-gr"))
				if c.quantita != nuovaQuantita:
					c.quantita = nuovaQuantita
					c.save()
					modificato = True


		
		if modificato:
			messages.info(request, "Modifiche effettuate con successo")
		return redirect(reverse('pivot', kwargs = {'pk' : ricetta.nome}))
	

	if request.method == "POST" and 'elimina' in request.POST:
		eliminaRicetta(request)
		return redirect('index')

	return render(request, 'app/modifica_ricetta.html', {'ricetta':ricetta,'tags':tags,
															'portate':portate,'ingredienti':ingredienti,'sonoManager':possoModificare,'chefs':chefs,'filtro':filtro})
	


@login_required(login_url='/login/')
def duplicaRicetta(request,pk,filtro):
	try:
		ricetta = Ricetta.objects.get(nome=pk.lower())
	except Ricetta.DoesNotExist:
		messages.error(request, ('Errore: ricetta non trovata'))
		return redirect('index')
	portate = Portata.objects.all()
	ingredienti = ingredientiRicettaConQuantita(ricetta)

	sonoManager = False

	if request.user.is_staff:
			chefs = list(Chef.objects.filter(manager=True))
			if ricetta.chef and ricetta.chef not in chefs: #il proprietario è uno chef normale e lo aggiungo alla lista
				chefs.append(ricetta.chef)
			chefs.append("")
	else:
		try:
			requestChef = Chef.objects.get(user = request.user) #sono uno chef..
			if requestChef.manager:	#..e sono un manager: chefs= tutti gli chef del mio impianto
				chefs = Chef.objects.filter(impianto=requestChef.impianto)
				sonoManager = True
			else: #..e non sono un manager: chefs= soltanto io
				chefs = [requestChef]
		except Chef.DoesNotExist:	#non sono uno chef: sono un capoarea
			sonoManager = True
			area = Area.objects.get(capo= CapoArea.objects.get(user=request.user))
			chefs = Chef.objects.filter( Q(impianto__area =  area) & Q(manager=True)) 


	tags = ricavaTagsDellaPortata(filtro)


	if request.method == "POST" and 'avanti' in request.POST:
		ingredientiCanc = request.POST.getlist('ingres')
		
		nome = str(request.POST['nome']).lower()		#input utente
		try: #se già esiste nel db la ricetta con quel nome allora non lo permetto
			ric = Ricetta.objects.get(nome__iexact=nome) 
			messages.error(request, ('La ricetta ' +nome+' già esiste nel sistema'))
			return redirect(reverse('duplicaricetta', kwargs = {'pk' : pk.lower(),'filtro':ricetta.portata}))
		except Ricetta.DoesNotExist:
			#la ricetta è nuova: procedo alla creazione
			nuova = Ricetta()
			nuova.nome = nome
			nuova.portata = Portata.objects.get(nome=str(request.POST.get('portata')))
			nuova.tag = Tag.objects.get(nome=str(request.POST.get('tag'))) 
			if len(request.FILES) != 0:
				nuova.foto = request.FILES['image']
			try:
				nuova.chef = Chef.objects.get(user = str(request.POST.get('chef')))
			except:
				nuova.chef = None
				#ricetta anonima: va bene
			nuova.save()
			
			for ing,q in ingredienti.items():
				nuovaQuantita = int(request.POST.get(ing.nome_generico+"-gr"))
				if nuovaQuantita != 0:
					content = Contenuto(ingrediente=ing, ricetta=nuova, quantita=nuovaQuantita)
					content.save()

			messages.success(request, ('Duplicato della ricetta creato con successo. Ora puoi inserire nuovi ingredienti'))
			return redirect(reverse('pivot', kwargs = {'pk' : nome}))

	return render(request, 'app/duplica_ricetta.html', {'ricetta':ricetta, 'portate':portate,'tags':tags,'ingredienti':ingredienti,'chefs':chefs,'sonoManager':sonoManager,'filtro':filtro})



@login_required(login_url='/login/')
def visualizzaImpianto(request,pk,year,month=""):
	try:	#controllo se l'impianto esiste o se qualcuno ha fatto il furbo
		impianto = Impianto.objects.get(nome=pk)
	except Impianto.DoesNotExist:
		messages.error(request, ('Impianto inesistente'))
		return redirect('index')

	if not request.user.is_staff:
		try:	#l'impianto esiste: controllo se user può accederci.
			chef = Chef.objects.get(user=request.user, impianto=impianto)
		except Chef.DoesNotExist:
			try:
				area = Area.objects.get(capo__user = request.user)
				if impianto.area != area:
					messages.error(request, ('Non hai i permessi per accedere a: ' + impianto.nome))
					return redirect('index')
			except Area.DoesNotExist:
				messages.error(request, ('Non hai i permessi per accedere a: ' + impianto.nome))
				return redirect('index')

	my_date = datetime.date.today()
	weekOggi,annoOggi = my_date.isocalendar()[1], my_date.isocalendar()[0]
	annoMax = annoOggi+5
	if year < 2021 or year > annoMax:
		messages.error(request, ("L'anno "+str(year) +" non è esistente nel sistema"))
		return redirect(reverse('impianto', kwargs = {'pk' : impianto.nome,'year':annoOggi}))
	
	classificazioni = ['Classico','Plus','Premium']

	if request.method == "POST" and 'cambia-classificazione' in request.POST:
		impianto.classificazione = request.POST.get('classificazione')
		impianto.save()
		messages.success(request, ("Classificazione aggiornata con successo"))
		return redirect(reverse('impianto', kwargs = {'pk' : impianto.nome,'year':annoOggi}))


	if request.method == "POST" and 'elimina' in request.POST:
		impiantoStr = request.POST.get('elimina')
		try:
			i = Impianto.objects.get(nome__iexact = impiantoStr)
			i.delete()
			messages.success(request, "Impianto '" +impiantoStr + "' eliminato con successo")
		except Impianto.DoesNotExist:
			messages.error(request, "Errore, impianto inesistente")
		return redirect('index')



	if request.method == "POST" and 'cambia' in request.POST:
		if request.POST['anno']:
			anno = int(request.POST['anno'])
			return redirect(reverse('impianto', kwargs = {'pk' : impianto.nome,'year':anno}))
		return redirect(reverse('impianto', kwargs = {'pk' : impianto.nome,'year':year}))


	settimane = calcolaEstremiSettimane(year)	#1: [x/xx/xx, x/xx/x]
	
	mesi = ['tutti i mesi','gennaio','febbraio','marzo','aprile','maggio','giugno','luglio','agosto','settembre','ottobre','novembre','dicembre']

	if month:
		month = month.lower()
		if month not in mesi:
			return redirect(reverse('impianto', kwargs = {'pk' : impianto.nome,'year':year}))
		settimane2 = dict()
		for n,estremi in settimane.items():
			mese_primo = estremi[0].split("/")[1]
			
			if (mese_primo == "01")  and month == "gennaio":
				settimane2[n] = estremi
			if (mese_primo == "02")  and month == "febbraio":
				settimane2[n] = estremi
			if (mese_primo == "03")  and month == "marzo":
				settimane2[n] = estremi
			if (mese_primo == "04")  and month == "aprile":
				settimane2[n] = estremi
			if (mese_primo == "05") and month == "maggio":
				settimane2[n] = estremi
			if (mese_primo == "06")  and month == "giugno":
				settimane2[n] = estremi
			if (mese_primo == "07")  and month == "luglio":
				settimane2[n] = estremi
			if (mese_primo == "08")  and month == "agosto":
				settimane2[n] = estremi
			if (mese_primo == "09") and month == "settembre":
				settimane2[n] = estremi
			if (mese_primo == "10")  and month == "ottobre":
				settimane2[n] = estremi
			if (mese_primo == "11")  and month == "novembre":
				settimane2[n] = estremi
			if (mese_primo == "12")  and month == "dicembre":
				settimane2[n] = estremi
		
		settimane = settimane2 #se ho selezionato un mese allora il diz avrà le settimane del mese
		

	for settimana,lista in settimane.items():
		menus = MenuSettimana.objects.filter(impianto=impianto,anno=year,settimana=settimana)
		if menus.count() == 0: 
			lista.append("danger")	#ROSSO: il menu non c'è
		else:	
			if approvato(menus):
				lista.append("success")	#VERDE: il menu c'è ed è approvato
			else: 
				lista.append("warning")	#GIALLO: il menu c'è ma deve essere approvato




	return render(request, 'app/impianto.html', {'year':year, 'impianto':impianto,'settimane':settimane,'weekOggi':weekOggi,'annoOggi':annoOggi,'annoMax':annoMax,'mesi':mesi,'month':month,'classificazioni':classificazioni})




@login_required(login_url='/login/')
def visualizzaSettimana(request,pk,sett,year):
	try:	
		impianto = Impianto.objects.get(nome__iexact=pk)
	except Impianto.DoesNotExist:
		messages.error(request, ('Impianto inesistente'))
		return redirect('index')

	if not request.user.is_staff:
		try:	#l'impianto esiste: controllo se user può accederci.
			chef = Chef.objects.get(user=request.user, impianto=impianto)
		except Chef.DoesNotExist:
			try:
				area = Area.objects.get(capo__user = request.user)
				if impianto.area != area:
					messages.error(request, ('Non hai i permessi per accedere a: ' + impianto.nome))
					return redirect('index')
			except Area.DoesNotExist:
				messages.error(request, ('Non hai i permessi per accedere a: ' + impianto.nome))
				return redirect('index')

	if sett>52 or sett==0:
		messages.error(request, ('Errore, settimana non trovata'))
		return redirect('index')

	
	annoOggi = datetime.date.today().year
	annoMax = annoOggi+5
	if year < 2021 or year > annoMax:
		return redirect(reverse('impianto', kwargs = {'pk' : impianto.nome,'year':year}))

	settimana = calcolaGiorniSettimana(year,sett) #diz Lunedi:23/12/2021..

	
	esisteMenu = MenuSettimana.objects.filter(impianto=impianto,anno=year, settimana=sett).exists()
		

	if esisteMenu:	#il menu esiste e quindi lo faccio visualizzare
		vedoBottoneApprova = False
		vedoBottoneEdit = False
		
		history = dict()
		listaMenuSettimana = []
		for giorno in settimana.keys():
			menu = MenuSettimana.objects.get(impianto=impianto,anno=year,settimana=sett,giorno=giorno)
			history[giorno] = HistoryMenu.objects.filter(menu=menu)
			listaMenuSettimana.append(menu)
		
		#posso approvare il menu solo se sono un admin ed il menu ancora non è approvato
		if (request.user.is_staff) and (approvato(listaMenuSettimana) == False):
			vedoBottoneApprova = True
		
		#posso modificare il menu se: sono il creatore | il manager dell'impianto | admin | capoarea
		capoArea = False
		chefManager = False
		try:
			chefManager = Chef.objects.get(user=request.user).manager
		except Chef.DoesNotExist:
			pass
			try:
				capoArea = Area.objects.get(capo__user = request.user)
			except Area.DoesNotExist:
				pass
		if (listaMenuSettimana[0].creatore == request.user) or (chefManager) or (request.user.is_staff) or (capoArea):
			vedoBottoneEdit = True

		aggiornato = getUltimaModifica(listaMenuSettimana)

		menuLunedi = listaMenuSettimana[0]
		creatore = menuLunedi.creatore.first_name + " "+ menuLunedi.creatore.last_name
		creazione = listaMenuSettimana[0].creazione

		if request.method == "POST" and 'genera-ordine' in request.POST:
			giorniOrdine = []
			for giorno in settimana.keys():
				if request.POST.get(giorno+"-ordine"):
					giorniOrdine.append(request.POST.get(giorno+"-ordine"))
			
			days =  "-".join(giorniOrdine)
			if len(days)>0:
				return redirect(reverse('generaordine', kwargs = {'pk' : impianto.nome,'year':year,'sett':sett,'days':days}))


		if request.method == "POST" and 'approva' in request.POST:
			#approvo tutti gli obj di menu della settimana
			for menu in listaMenuSettimana:
				menu.approvatore = request.user
				menu.save()
			return redirect(reverse('settimane', kwargs = {'pk' : impianto.nome,'year':year,'sett':sett}))


		costi = False
		allergeni = False
		if request.method == "POST" and 'VisualizzaNormale' in request.POST:
			costi=False
			allergeni= False
			return redirect(reverse('settimane', kwargs = {'pk' : impianto.nome,'year':year,'sett':sett}))


		if request.method == "POST" and 'VisualizzaCosti' in request.POST:
			costi=True

			costoGiorni = calcolaCostiSettimana(impianto,year,sett,settimana.keys())

			costoSettimana = round(media(costoGiorni),2)

			ricetteCosti = dict()
			for menu in listaMenuSettimana:
				for ricetta in menu.ricette.all():
					if ricetta not in ricetteCosti:
						ricetteCosti[ricetta] = calcolaCostoRicetta(ricetta, impianto)
		

			return render(request, 'app/settimana.html', {'listaMenuSettimana':listaMenuSettimana,'impianto':impianto, 'esisteMenu':esisteMenu,'settimana':settimana, 'vedoBottone':vedoBottoneApprova, 'vedoBottoneEdit':vedoBottoneEdit, 'sett':sett, 'year':year,'costi':costi,'costoGiorni':costoGiorni,'costoSettimana':costoSettimana,'aggiornato':aggiornato,'ricetteCosti':ricetteCosti,'history':history,'creatore':creatore,'creazione':creazione})
		

		if request.method == "POST" and 'VisualizzaAllergeni' in request.POST:
			allergeni=True
			calorie = dict()

			allergeniTotali = set()
			ricetteAllergeni = dict()
			for menu in listaMenuSettimana:
				for ricetta in menu.ricette.all():
					if ricetta not in ricetteAllergeni.keys():
						insieme = allergeniRicetta(ricetta)
						ricetteAllergeni[ricetta] = insieme
						allergeniTotali = allergeniTotali|set(insieme) #unione
					if ricetta not in calorie.keys():
						calorie[ricetta] = calorieRicetta(ricetta)

			allergeniTotali = sorted([allergene.nome for allergene in allergeniTotali])
			return render(request, 'app/settimana.html', {'listaMenuSettimana':listaMenuSettimana,'impianto':impianto, 'esisteMenu':esisteMenu,'settimana':settimana, 'vedoBottone':vedoBottoneApprova, 'vedoBottoneEdit':vedoBottoneEdit, 'sett':sett, 'year':year,'allergeni':allergeni,'ricetteAllergeni':ricetteAllergeni,'allergeniTotali':allergeniTotali,'aggiornato':aggiornato,'history':history,'creatore':creatore,'creazione':creazione,'calorie':calorie})		



		return render(request, 'app/settimana.html', {'listaMenuSettimana':listaMenuSettimana,'impianto':impianto, 'esisteMenu':esisteMenu,'settimana':settimana, 'vedoBottone':vedoBottoneApprova,'vedoBottoneEdit':vedoBottoneEdit, 'sett':sett, 'year':year,'costi':costi,'allergeni':allergeni,'aggiornato':aggiornato,'history':history,'creatore':creatore,'creazione':creazione})



	else:	#il menu NON esiste e quindi lo faccio creare
		tags = Tag.objects.all() 
		tagsList = Tag.objects.all() 

		conteggi = dict()
		ricette = dict()

		if request.user.is_staff: #un admin può importare anche i menu degli altri impianto
			impianti = Impianto.objects.all()
		else: #uno chef può importare solo i menu del proprio impianto
			try:
				if Chef.objects.get(user=request.user):
					impianti = [impianto]
			except Chef.DoesNotExist:
				#non sono un admin e nè chef: sono capoarea
				impianti = Impianto.objects.filter(area=Area.objects.get(capo__user=request.user))
	
		daImportare = dict()
		for imp in impianti: #itero sugli impianti che posso importare
			dizio = dict()
			daImportare[imp] = dizio
			anni = set(MenuSettimana.objects.filter(impianto=imp).values_list('anno',flat=True))
			for a in anni:
				dizio[a] = sorted(set(MenuSettimana.objects.filter(impianto=imp,anno=a).values_list('settimana',flat=True)))
			daImportare[imp] = dizio


		importa = False
		if request.method == "POST" and 'importa' in request.POST:
			for tag in tags:
				if impianto.classificazione == "Classico":
					query = Ricetta.objects.filter( Q(tag=tag) & Q(special=False)  & (Q(approvata=True) | Q(chef__impianto=impianto)))
				else:
					query = Ricetta.objects.filter( Q(tag=tag) & (Q(approvata=True) | Q(chef__impianto=impianto)))
				ricette[tag] = query
				conteggi[tag] = query.count()

			importa = True
			lista = request.POST.get("importa").split("-")
			impiantoImport = str(lista[0])
			settimanaN = int(lista[1])
			anno = int(lista[2])
			ricetteSettimana = getRicetteSettimana(impiantoImport,anno,settimanaN,settimana.keys())	


			return render(request, 'app/ricette_menu.html', {'sett':sett,'year':year,'impianto':impianto
													  ,'ricette':ricette,'settimana':settimana,'esisteMenu':esisteMenu,'conteggi':conteggi,'importa':importa,'ricetteSettimana':ricetteSettimana})


		if request.method == "POST" and 'avanti' in request.POST:
			for giorno in settimana.keys():
				#controllo se ho fatto il furbo creando obj menu e tornando subito indietro
				try:
					if MenuSettimana.objects.get(impianto=impianto,anno=year,settimana=sett,giorno=giorno):
						messages.error(request, ('Attenzione: il menu della settimana '+str(sett)+' del ' +str(year)+' già esiste'))
						return redirect(reverse('impianto', kwargs = {'pk' : impianto.nome,'year':year}))
				except:
					pass
			numTags = int(request.POST.get('numTags'))

			tagScelti = dict()
			for giorno,data in settimana.items():
				tagScelti[giorno] = []
				for i in range(1,numTags+1):
					if request.POST.get(str(i)+giorno):
						stringa = request.POST.get(str(i)+giorno)
						t = Tag.objects.get(nome=stringa)
						tagScelti[giorno].append(t)
			
			for tag in tags:
				if request.POST.get('soloRicetteImpianto') == "yes":	
					if impianto.classificazione == "Classico":
						query = Ricetta.objects.filter( Q(tag=tag) & Q(special=False)  &  Q(chef__impianto=impianto))
					else:
						query = Ricetta.objects.filter( Q(tag=tag) & Q(chef__impianto=impianto))
				else:
					if impianto.classificazione == "Classico":
						query = Ricetta.objects.filter( Q(tag=tag) & Q(special=False)  & (Q(approvata=True) | Q(chef__impianto=impianto)))
					else:
						query = Ricetta.objects.filter( Q(tag=tag) & (Q(approvata=True) | Q(chef__impianto=impianto)))
				ricette[tag] = query
				conteggi[tag] = query.count()


			return render(request, 'app/ricette_menu.html', {'sett':sett,'year':year,'impianto':impianto
													  ,'ricette':ricette,'settimana':settimana,'esisteMenu':esisteMenu,'tagScelti':tagScelti,'conteggi':conteggi,'numTags':numTags})
		


		if request.method == "POST" and 'salva' in request.POST:
			#controllo se già esiste un menu per il giorno corrente
			if MenuSettimana.objects.filter(impianto=impianto,anno=year,settimana=sett).exists():
				messages.error(request, ('Attenzione: il menu della settimana '+str(sett)+' del ' +str(year)+' già esiste'))
				return redirect(reverse('impianto', kwargs = {'pk' : impianto.nome,'year':year}))

			ricetteGiorni = dict()
			numTags = int(request.POST.get('numTags'))
			almenoUna = False
			for giorno in settimana.keys():
				ricetteGiorni[giorno] = set()

				for j in range(1,numTags+1):
					ricettaStr = request.POST.get(giorno+"-"+str(j))
					if ricettaStr == None or ricettaStr == "":
						continue #ricetta non seleziona oppure sono arrivato alla fine: vado avanti
					else:
						ricettaObj = Ricetta.objects.get(nome=str(ricettaStr))
						ricetteGiorni[giorno].add(ricettaObj)
						if not almenoUna:
							almenoUna=True
		

			if almenoUna: #è stata selezionata almeno una ricetta
				for giorno,ricettes in ricetteGiorni.items():
					creatore = User.objects.get(username=request.user.username)
					dayObj = MenuSettimana(impianto=impianto,anno=year,settimana=sett,giorno=giorno,creatore=creatore)
					dayObj.save()
					for ricetta in ricettes:
						dayObj.ricette.add(ricetta)
			else: #non è stato selezionata nessuna ricette: ritorno alla stessa pagina
				messages.error(request, ('Non puoi creare il menu senza selezionare almeno una ricetta'))
				return HttpResponseRedirect(request.path_info)

			messages.success(request, ("Menu delle settimana "+ str(sett) +" creato con successo"))
			return redirect(reverse('settimane', kwargs = {'pk' : impianto.nome,'year':year,'sett':sett}))


		if request.method == "POST" and 'cambiaNumeroTags' in request.POST:
			tagsList = list(tags)
			nuovo = int(request.POST.get('numTags'))
			if nuovo <= tags.count():
				tagsList = tagsList[:nuovo]
			else:
				nuovi = nuovo -tags.count()
				[tagsList.append("-------") for n in range(0,nuovi)]
	
			return render(request, 'app/settimana.html', {'sett':sett,'year':year,'impianto':impianto,'settimana':settimana,'esisteMenu':esisteMenu,'daImportare':daImportare,'tags':tags,'tagsList':tagsList})


		return render(request, 'app/settimana.html', {'sett':sett,'year':year,'impianto':impianto,'settimana':settimana,'esisteMenu':esisteMenu,'daImportare':daImportare,'tags':tags,'tagsList':tagsList})




class DownloadPDFSettimana(View):
	def get(self,request,*args,**kwargs):
		impianto = Impianto.objects.get(nome=kwargs['pk']) 
		year = kwargs['year']
		sett = kwargs['sett']
		settimana = calcolaGiorniSettimana(year,sett)
		ricetteSettimana = getRicetteSettimana(impianto,year,sett,settimana.keys())

		data = {'impianto':impianto,'settimana':settimana, 'sett':sett, 'year':year, 'ricetteSettimana':ricetteSettimana}


		pdf = render_to_pdf('app/pdf_menu_settimana.html',data)

		response = HttpResponse(pdf,content_type='application/pdf')
		filename = "Menu_settimana%s_%s_%s.pdf" %(sett,year,impianto.nome)
		content = "attachment; filename=%s" %(filename)
		response['Content-Disposition'] = content
		return response


class DownloadPDFSettimanaRicettario(View):
	def get(self,request,*args,**kwargs):
		impianto = Impianto.objects.get(nome=kwargs['pk']) 
		year = kwargs['year']
		sett = kwargs['sett']
		settimana = calcolaGiorniSettimana(year,sett)
		
		diz = dict()
		for giorno in settimana.keys():
			ricette = getRicetteGiornoOrdinate(impianto,year,sett,giorno)
			quantita = dict()
			for ricetta in ricette:
				quantita[ricetta] = Contenuto.objects.filter(ricetta=ricetta).order_by("-quantita")
			diz[giorno] = quantita


		data = {'impianto':impianto,'settimana':settimana, 'sett':sett, 'year':year,'diz':diz}


		pdf = render_to_pdf('app/pdf_menu_settimana_ricettario.html',data)

		response = HttpResponse(pdf,content_type='application/pdf')
		filename = "ricettario_settimana%s_%s_%s.pdf" %(sett,year,impianto.nome)
		content = "attachment; filename=%s" %(filename)
		response['Content-Disposition'] = content
		return response




class DownloadPDFGiorno(View):
	def get(self,request,*args,**kwargs):
		impianto = Impianto.objects.get(nome=kwargs['pk']) 
		year = kwargs['year']
		sett = kwargs['sett']
		day = kwargs['day']

		settimana = calcolaGiorniSettimana(year,sett)

		giorno = settimana[day]

		ricetteSettimana = getRicetteSettimana(impianto,year,sett,[day])

		data = {'impianto':impianto,'settimana':settimana,'sett':sett, 'year':year, 'ricetteSettimana':ricetteSettimana}


		pdf = render_to_pdf('app/pdf_menu_settimana.html',data)

		response = HttpResponse(pdf,content_type='application/pdf')
		filename = "Menu_%s_%s.pdf" %(giorno,impianto.nome)
		content = "attachment; filename=%s" %(filename)
		response['Content-Disposition'] = content
		return response



@login_required(login_url='/login/')
def analisiIngredienti(request,pk,sett,year):
	try:	#controllo se l'impianto esiste o se qualcuno ha fatto il furbo
		impianto = Impianto.objects.get(nome__iexact=pk)
	except Impianto.DoesNotExist:
		messages.error(request, ('Impianto inesistente'))
		return redirect('index')
	if not request.user.is_staff:
		try:	#l'impianto esiste: controllo se user può accederci.
			chef = Chef.objects.get(user=request.user, impianto=impianto)
		except Chef.DoesNotExist:
			try:
				area = Area.objects.get(capo__user = request.user)
				if impianto.area != area:
					messages.error(request, ('Non hai i permessi per accedere a: ' + impianto.nome))
					return redirect('index')
			except Area.DoesNotExist:
				messages.error(request, ('Non hai i permessi per accedere a: ' + impianto.nome))
				return redirect('index')
	if sett>52 or sett==0:
		messages.error(request, ('Errore, settimana non trovata'))
		return redirect('index')

	settimana = calcolaGiorniSettimana(year,sett) #diz Lunedi:23/12/2021..
	portate = Portata.objects.all()
	tags = Tag.objects.all()

	settt = sett-4
	anno = year
	if settt <= 0:
		anno = year-1
		settt = sett-4 + 52

	estremoSx = calcolaEstremiSettimana(anno,settt)[0]
	estremoDx = calcolaEstremiSettimana(year,sett)[1]

	nature = ['Primario','Secondario']

	if request.method == "POST" and 'esegui' in request.POST:
		portateSelezionate = request.POST.getlist('portate')
		tagsSelezionati =  request.POST.getlist('tags')
		natureSelezionate =  request.POST.getlist('nature')
		
		voglio_primari = 'Primario' in natureSelezionate
		voglio_secondari = 'Secondario' in natureSelezionate

		ingCountPrimari = dict()
		ingCountSecondari = dict()
		for i in range(0,5):
			sett_nuova = sett-i
			anno = year
			if sett-i <= 0:
				anno = year-1
				sett_nuova = sett-i + 52
			
			try:
				ricetteSettimana = getRicetteSettimana(impianto, year, sett_nuova, settimana.keys())
			except MenuSettimana.DoesNotExist:
				continue
			for giorno,lista in ricetteSettimana.items():
				for ricetta in lista:
					if (ricetta.portata.nome in portateSelezionate) and (ricetta.tag.nome in tagsSelezionati):
						ing = ingredientiRicettaConQuantita(ricetta)
						for ingrediente,q in ing.items():
							if q >= 50 and voglio_primari:
								if ingrediente not in ingCountPrimari.keys():
									ingCountPrimari[ingrediente] = 1
								else:
									ingCountPrimari[ingrediente]+= 1
							elif q < 50 and voglio_secondari:
								if ingrediente not in ingCountSecondari.keys():
									ingCountSecondari[ingrediente] = 1
								else:
									ingCountSecondari[ingrediente]+= 1

		ingCount = dict()
		for ing,tot in ingCountPrimari.items():
			ingCount[ing] = [tot,0]
		for ing,tot in ingCountSecondari.items():
			if ing in ingCount:
				ingCount[ing][1] = tot
			else:
				ingCount[ing] = [0,tot]

	
		return render(request, 'app/analisi_ingredienti_effettuata.html', {'impianto':impianto,'sett':sett, 'year':year, 'ingCount':ingCount,'portateSelezionate':portateSelezionate, 'tagsSelezionati':tagsSelezionati, 'natureSelezionate':natureSelezionate})

	return render(request, 'app/analisi_ingredienti.html', {'nature':nature,'portate':portate,'tags':tags,'sett':sett,'year':year,'estremoSx':estremoSx,'estremoDx':estremoDx})



@login_required(login_url='/login/')
def analisiPiatti(request,pk,sett,year):
	try:	#controllo se l'impianto esiste o se qualcuno ha fatto il furbo
		impianto = Impianto.objects.get(nome=pk)
	except Impianto.DoesNotExist:
		messages.error(request, ('Impianto inesistente'))
		return redirect('index')
	if not request.user.is_staff:
		try:	#l'impianto esiste: controllo se user può accederci.
			chef = Chef.objects.get(user=request.user, impianto=impianto)
		except Chef.DoesNotExist:
			try:
				area = Area.objects.get(capo__user = request.user)
				if impianto.area != area:
					messages.error(request, ('Non hai i permessi per accedere a: ' + impianto.nome))
					return redirect('index')
			except Area.DoesNotExist:
				messages.error(request, ('Non hai i permessi per accedere a: ' + impianto.nome))
				return redirect('index')
	if sett>52 or sett==0:
		messages.error(request, ('Errore, settimana non trovata'))
		return redirect('index')


	portate = Portata.objects.all()
	tags = Tag.objects.all()

	settt = sett-4
	anno = year
	if settt <= 0:
		anno = year-1
		settt = sett-4 + 52

	estremoSx = calcolaEstremiSettimana(anno,settt)[0]
	estremoDx = calcolaEstremiSettimana(year,sett)[1]

	settimana = calcolaGiorniSettimana(year,sett)


	if request.method == "POST" and 'esegui' in request.POST:
		portateSelezionate = request.POST.getlist('portate')
		tagsSelezionati = request.POST.getlist('tags')
		
		conteggi = dict()

		for i in range(0,5):
			sett_nuova = sett-i
			anno = year
			if sett-i <= 0:
				anno = year-1
				sett_nuova = sett-i + 52
			#print('Ricavo le ricette dalla settimana '+ str(sett_nuova))
			try:
				ricette = getRicetteSettimana(impianto, year, sett_nuova, settimana.keys() )
	
			except MenuSettimana.DoesNotExist:
				#non esistono ricette per la settimana
				continue

			for giorno,lista_ricette in ricette.items():
				for ricetta in lista_ricette:
					if (ricetta.tag.nome in tagsSelezionati) and (ricetta.portata.nome in portateSelezionate):
						if ricetta not in conteggi:
							conteggi[ricetta] = 1
						else:
							conteggi[ricetta] += 1
		
		conteggi = {k: v for k, v in sorted(conteggi.items(), key=lambda item: -item[1])}

		return render(request, 'app/analisi_piatti_effettuata.html', {'impianto':impianto,'conteggi':conteggi,'year':year,'sett':sett,'portateSelezionate':portateSelezionate,'tagsSelezionati':tagsSelezionati})



	return render(request, 'app/analisi_piatti.html', {'portate':portate,'tags':tags,'year':year,'sett':sett,'estremoSx':estremoSx,'estremoDx':estremoDx})



@login_required(login_url='/login/')
def modificaMenu(request,pk,sett,year):
	try:	#controllo se l'impianto esiste o se qualcuno ha fatto il furbo
		impianto = Impianto.objects.get(nome=pk)
	except Impianto.DoesNotExist:
		messages.error(request, ('Impianto inesistente'))
		return redirect('index')
	if not request.user.is_staff:
		try:	#l'impianto esiste: controllo se user può accederci.
			chef = Chef.objects.get(user=request.user, impianto=impianto)
		except Chef.DoesNotExist:
			try:
				area = Area.objects.get(capo__user = request.user)
				if impianto.area != area:
					messages.error(request, ('Non hai i permessi per accedere a: ' + impianto.nome))
					return redirect('index')
			except Area.DoesNotExist:
				messages.error(request, ('Non hai i permessi per accedere a: ' + impianto.nome))
				return redirect('index')
	if sett>52 or sett==0:
		messages.error(request, ('Errore, settimana non trovata'))
		return redirect('index')
	if not MenuSettimana.objects.filter(impianto=impianto,anno=year, settimana=sett).exists():
		messages.error(request, ('Attenzione: il menu desiderato non esiste'))
		return redirect(reverse('impianto', kwargs = {'pk' : impianto.nome,'year':year}))
	
	#posso modificare il menu se sono il creatore | il manager dell'impianto | admin | capoArea
	chefManager = False
	capoArea = False
	try:
		chefIo = Chef.objects.get(user=request.user)
		chefManager = chefIo.manager
	except Chef.DoesNotExist:
		try:
			capoArea = Area.objects.get(capo__user = request.user)
		except Area.DoesNotExist:
			pass
	menu = MenuSettimana.objects.get(impianto=impianto.nome,anno=year, settimana=sett,giorno="Lunedi")
	if not ((menu.creatore == request.user) or (chefManager) or (request.user.is_staff) or (capoArea)):
		return redirect(reverse('settimane', kwargs = {'pk' : impianto.nome,'year':year,'sett':sett}))

	aggiunta = False

	settimana = calcolaGiorniSettimana(year,sett) #diz Lunedi:23/12/2021

	tags= Tag.objects.all()

	ricetteSettimana = getRicetteSettimana(impianto,year,sett,settimana.keys())
	

	
	if request.method == "POST" and 'aggiunta' in request.POST:
		tagIndici = dict()	#per ogni giorno associo gli n indici mancanti (per arrivare a len(tags))
		aggiunta=True

		tagsList = []
		insCheck = set()
		for giorno,data in settimana.items():
			nuovi = int(request.POST.get(giorno))
			insCheck.add(nuovi)
			tagIndici[giorno] = []
			[tagIndici[giorno].append("-------") for n in range(0,nuovi)]
		if (len(insCheck) == 1) and 0 in insCheck:
			return redirect(reverse('settimane', kwargs = {'pk' : impianto.nome,'year':year,'sett':sett}))
		


		return render(request, 'app/modifica_menu.html', {'aggiunta':aggiunta,'sett':sett,'year':year, 'impianto':impianto, 'settimana':settimana, 'tagIndici':tagIndici,'ricetteSettimana':ricetteSettimana,'tags':tags})



	if request.method == "POST" and 'elimina' in request.POST:
		ricetteCanc = request.POST.getlist("cancella")
		elim = dict()
		for el in ricetteCanc:
			lista = el.split('-')
			giorno = lista[0]
			ricetta = Ricetta.objects.get(nome=lista[1])
			
			if giorno in elim:
				elim[giorno].append(ricetta)
			else:
				elim[giorno] = [ricetta]
		
		for giorno,ricette in elim.items():
			text = ""
			menu = MenuSettimana.objects.get(impianto=impianto,anno=year, settimana=sett,giorno=giorno)
			history = HistoryMenu()
			history.menu = menu
			history.text = text
			history.user = request.user
			for ricetta in ricette:
				if ricetta in menu.ricette.all():
					menu.ricette.remove(ricetta)
					text+= "Ha eliminato la ricetta " + ricetta.nome + "\n"
			if text:
				history.text = text
				history.save()
				#ho effettuato modifiche: eliminato approvazione al giorno
				menu.approvatore = None
				menu.save()

			
		return redirect(reverse('modificamenu', kwargs = {'pk' : impianto.nome,'year':year,'sett':sett}))


	if request.method == "POST" and 'avanti' in request.POST:
		tagScelti = dict()
		okVaiAvanti = False
		for giorno,data in settimana.items():
			tagScelti[giorno] = []
			
			for i in range(1,50):
				tagScelto = request.POST.get(str(i)+giorno)
				if tagScelto != "" and tagScelto != None:
					tagScelti[giorno].append(Tag.objects.get(nome=tagScelto))
					okVaiAvanti = True

		if okVaiAvanti == False:
			messages.error(request, ('Seleziona almeno un tag'))
			return HttpResponseRedirect(request.path_info)
		

		conteggi = dict()
		ricette = dict()
		for tag in tags:
			ricetteQuery = Ricetta.objects.filter(Q(tag=tag) & (Q(approvata=True) | Q(chef__impianto=impianto)))
			conteggi[tag] = ricetteQuery.count()
			ricette[tag] = ricetteQuery



		return render(request, 'app/ricette_menu_modifica.html', {'sett':sett,'year':year,'impianto':impianto
												  ,'ricette':ricette,'settimana':settimana,'tagScelti':tagScelti,'conteggi':conteggi})


	if request.method == "POST" and 'salva' in request.POST:
		for giorno,data in settimana.items():
			text = ""
			dayObj = MenuSettimana.objects.get(impianto=impianto,anno=year,settimana=sett,giorno=giorno)
			i = 1
			while request.POST.get(giorno+"-"+str(i)):
				ricettaStr = str(request.POST.get(giorno+"-"+str(i)))
				ricettaObj = Ricetta.objects.get(nome=ricettaStr)
				if ricettaObj not in dayObj.ricette.all():
					dayObj.ricette.add(ricettaObj)
					text+= "Ha aggiunto la ricetta " + ricettaStr + "\n"
				i+=1

			#tengo traccia dell'aggiunta (se c'è stata)
			if text != "":
				history = HistoryMenu()
				history.menu = dayObj
				history.text = text
				history.user = request.user
				history.save()
				#ho effettuato modifiche: eliminato approvazione al giorno
				dayObj.approvatore = None
				dayObj.save()

		
		return redirect(reverse('settimane', kwargs = {'pk' : impianto.nome,'year':year,'sett':sett}))


	return render(request, 'app/modifica_menu.html', {'aggiunta':aggiunta,'sett':sett,'year':year, 'impianto':impianto, 'settimana':settimana, 'ricetteSettimana':ricetteSettimana})



@login_required(login_url='/login/')
def generaOrdine(request,pk,sett,year,days):
	try:	#controllo se l'impianto esiste o se qualcuno ha fatto il furbo
		impianto = Impianto.objects.get(nome__iexact=pk)
	except Impianto.DoesNotExist:
		messages.error(request, ('Impianto inesistente'))
		return redirect('index')
	if not request.user.is_staff:
		try:	#l'impianto esiste: controllo se user può accederci.
			chef = Chef.objects.get(user=request.user, impianto=impianto)
		except Chef.DoesNotExist:
			try:
				area = Area.objects.get(capo__user = request.user)
				if impianto.area != area:
					messages.error(request, ('Non hai i permessi per accedere a: ' + impianto.nome))
					return redirect('index')
			except Area.DoesNotExist:
				messages.error(request, ('Non hai i permessi per accedere a: ' + impianto.nome))
				return redirect('index')
	if sett>52 or sett==0:
		messages.error(request, ('Errore, settimana non trovata'))
		return redirect('index')
	
	settimana = calcolaGiorniSettimana(year,sett) #diz Lunedi:23/12/2021

	
	giorni = days.split('-')
	
	for giorno in giorni:
		if giorno not in settimana.keys():
			return redirect(reverse('settimane', kwargs = {'pk' : impianto.nome,'year':year,'sett':sett}))


	queryRicette = MenuSettimana.objects.filter( Q(impianto=impianto) & Q(anno=year) & Q(settimana=sett) & Q(giorno__iregex=r'(' + '|'.join(giorni) + ')')).values_list('ricette',flat=True)

	if (None in queryRicette) and (len(set(queryRicette))==1):
		return redirect(reverse('settimane', kwargs = {'pk' : impianto.nome,'year':year,'sett':sett}))

	ricetteGiorni = []
	for nome in queryRicette:
		try:
			ricetta = Ricetta.objects.get(nome__iexact=nome)
			ricetteGiorni.append(ricetta)
		except Ricetta.DoesNotExist:
			continue

	listaPorzioni = [1 for x in ricetteGiorni]

	fornitori = set()
	for ricetta in ricetteGiorni:
		ingredienti = ingredientiRicettaConQuantita(ricetta)
		for ing in ingredienti.keys():
			fornitore = IngredienteImpianto.objects.get(ingrediente=ing,impianto=impianto).fornitore
			if fornitore != None:
				fornitori.add(fornitore)

	conteggi = dict()
	for ricetta in ricetteGiorni:
		conteggi[ricetta] = ricetteGiorni.count(ricetta)

	ricetteGiorni = set(ricetteGiorni)



	if request.method == "POST" and 'genera' in request.POST:
		fornitoreSelezionato = request.POST.get('fornitore')
		fornitoriSelect = []
		if fornitoreSelezionato:
			fornitoriSelect.append(Fornitore.objects.get(nome= request.POST.get('fornitore')))
		else: #tutti i fornitori
			fornitoriSelect = list(fornitori)
			fornitoriSelect.append(None)
		
		diz= dict()
		for i,ricetta in enumerate(ricetteGiorni):
			listaPorzioni[i] = int(request.POST.get(ricetta.nome))

			ingredienti = ingredientiRicettaConQuantita(ricetta)


			for ing,q in ingredienti.items():
				fornitore = IngredienteImpianto.objects.get(ingrediente=ing,impianto=impianto).fornitore
				if fornitore in fornitoriSelect:
					if ing not in diz:
						diz[ing] = q * listaPorzioni[i]
					else:
						diz[ing]+= q* listaPorzioni[i]
		
		totale = 0.0
		for ing,tot in diz.items():
			obj = IngredienteImpianto.objects.get(impianto=impianto,ingrediente=ing)
			listino = obj.listino
			fornitore = obj.fornitore
			prezzo = round(round(listino * tot / 1000, 2),   2)
			totale+=prezzo
			diz[ing] = [fornitore,tot/1000,prezzo]
		totale = str(round(totale,2))
		

		#per pdf: pip install xhtml2pdf
		data = {'ricetteGiorni':ricetteGiorni,'giorni':giorni,'listaPorzioni':listaPorzioni,'diz':diz,'totale':totale,'impianto':impianto,'sett':sett,'year':year,'fornitoreSelezionato':fornitoreSelezionato,'settimana':settimana}
		pdf = render_to_pdf('app/pdf_genera_ordine.html',data)

		response= HttpResponse(pdf,content_type="application/pdf")
		if fornitoreSelezionato:
			filename = "ordine_{}_{}.pdf".format(impianto.nome,fornitoreSelezionato)
		else:
			filename = "ordine_{}.pdf".format(impianto.nome)
		content = "filename=%s" %(filename)
		response['Content-Disposition'] = content
		return response

		
	return render(request, 'app/genera_ordine.html', {'ricetteGiorni':ricetteGiorni,'listaPorzioni':listaPorzioni,'fornitori':fornitori,'impianto':impianto,'giorni':giorni,'sett':sett,'conteggi':conteggi,'settimana':settimana})





############################## FUNZIONI AUSILIARIE ####################################################


#data una ricetta in input crea la tabella pivot
def creaTabellaPivot(ricetta,impianti=None):
	diz = creaDizPivot(ricetta,impianti)	#diz
	complessivo = calcolaComplessivoPivot(diz)	#lista
	allergeni = [allergene.nome for allergene in allergeniRicetta(ricetta)]
	return diz, complessivo, allergeni


#ritorna il diz dei valori di ogni ingrediente e la lista degli allergeni totali
def creaDizPivot(ricetta,impianti=None):
	ingredienti = ingredientiRicettaConQuantita(ricetta)
	allergeni = [allergene.nome for allergene in allergeniRicetta(ricetta)]
	pivot = dict()
	for ing,q in ingredienti.items():
		allergeniIng = [Allergene.objects.get(nome = al.nome).nome for al in ing.allergeni.all()]

		if impianti: #sono chef | capoarea
			listini = []
			for impianto in impianti:
				prezzoKg = IngredienteImpianto.objects.get(ingrediente=ing,impianto=impianto).listino
				listini.append(prezzoKg)

			mediaListino = round(media(listini), 2)
			prezzo = mediaListino * q / 1000
		else: #sono un admin
			listino = ing.listino
			prezzo = listino * q / 1000


		pivot[ing] =    [q, 								#quantita
					 	(round(prezzo, 2)),					#costo
						calorieIngrediente(ing,q), 			#calorie
						carboidratiIngrediente(ing,q),		#carboidrati
						proteineIngrediente(ing,q),			#proteine
						grassiIngrediente(ing,q),			#grassi
						allergeniIng						#lista allergeni
						]

	return pivot


def calorieIngrediente(ingrediente,q):
	return int(round(ingrediente.energiaKcal * q / 100, 0))

def carboidratiIngrediente(ingrediente,q):
	return int(round(ingrediente.glucidiTot * q / 100, 0))

def proteineIngrediente(ingrediente,q):
	return float(round(ingrediente.protTot * q / 100, 1))

def grassiIngrediente(ingrediente,q):
	return float(round(ingrediente.lipidiTot * q / 100, 1))


def calorieRicetta(ricetta):
	diz = ingredientiRicettaConQuantita(ricetta)
	tot = 0
	for ing,q in diz.items():
		tot+= calorieIngrediente(ing,q)
	return tot


#Dato il dizionario con tutti i valori degli ingredienti di una ricetta: calcola le somme.
def calcolaComplessivoPivot(diz):
	complessivo = []
	#definisco di quante colonne devo fare la somma
	for lista in diz.values():
		for i in range(len(lista)-1):	
			complessivo.append(0)
		break

	for ing,lista in diz.items():
		for i,el in enumerate(lista):
			if not isinstance(el, list):
				complessivo[i]+= el
	for i,n in enumerate(complessivo):
		if isinstance(n, float):
			complessivo[i] = "{0:.2f}".format(n)
			complessivo[i] = float(complessivo[i])
	
	return complessivo


#data una ricetta ritorna l'insieme dei suoi allergeni in ordine alfabetico
def allergeniRicetta(ricetta):
	allergeni = set()
	ingredienti = ingredientiRicettaConQuantita(ricetta)
	for ing in ingredienti.keys():
		if ing.allergeni.all():
			for allergene in ing.allergeni.all():
					allergeni.add(allergene.nome)
	ordinati = sorted(list(allergeni))
	return [Allergene.objects.get(nome=nome) for nome in ordinati]


def ingredientiRicettaConQuantita(ricetta):
	diz = dict()
	contenuti = Contenuto.objects.filter(ricetta=ricetta).values_list('ingrediente','quantita').order_by('-quantita')
	for stringa,q in contenuti:
		ing = Ingrediente.objects.get(nome_generico = stringa) 
		diz[ing] = int(q)

	return diz
	


def media(lista): 
    return sum(lista)/len(lista)


#ritorna un dizionario dei 5 giorni di una settimana di un certo anno
def calcolaGiorniSettimana(year,sett):
	diz = dict()
	first = date(year, 1, 1)
	base = 1 if first.isocalendar()[1] == 1 else 8
	giorni = ['Lunedi','Martedi','Mercoledi','Giovedi','Venerdi']
	for i,giorno in enumerate(giorni, start=0):
		giornoDateTime = first + timedelta(days=base - first.isocalendar()[2] + 7 * (sett - 1) + i)
		diz[giorno] = giornoDateTime.strftime('%d/%m/%Y')
	return diz



#ritorna un diz con il lunedi e la domenica di ogni settimana di un certo anno
def calcolaEstremiSettimane(year):
	first = date(year, 1, 1)
	print(first)
	print(first.isocalendar())
	base = 1 if first.isocalendar()[1] == 1 else 8
	diz = dict()
	for i in range(1,53):
		lunedi = first + timedelta(days=base - first.isocalendar()[2] + 7 * (i - 1))
		domenica = first + timedelta(days=base - first.isocalendar()[2] + 7 * (i - 1) + 6)
		diz[i] = [lunedi.strftime('%d/%m/%Y'), domenica.strftime('%d/%m/%Y')]
	return diz


def calcolaEstremiSettimana(year,i):
	first = date(year, 1, 1)
	base = 1 if first.isocalendar()[1] == 1 else 8
	lunedi = first + timedelta(days=base - first.isocalendar()[2] + 7 * (i - 1))
	domenica = first + timedelta(days=base - first.isocalendar()[2] + 7 * (i - 1) + 6)
	return [lunedi.strftime('%d/%m/%Y'), domenica.strftime('%d/%m/%Y')]


#Data una ricetta calcola il suo costo totale in un certo impianto
def calcolaCostoRicetta(ricetta,impianto):
	totale = 0.0
	ingRicetta = ingredientiRicettaConQuantita(ricetta)
	for ing,q in ingRicetta.items():
		prezzo = IngredienteImpianto.objects.get(ingrediente=ing,impianto=impianto).listino
		totale+= round(prezzo * q / 1000, 2)
		#totale+= float("{0:.2f}".format(prezzo))
	return round(totale,2)


#Calcola i costi dei 5 giorni di una certa settimana per il menu di un impianto, in un certo anno
def calcolaCostiSettimana(impianto,year,sett,giorni):
	ricetteSettimana = getRicetteSettimana(impianto,year,sett,giorni)
	costoTotale = [0.0 for g in ricetteSettimana.keys()]
	primi = ricavaTagsDellaPortata('Primo piatto')
	secondi = ricavaTagsDellaPortata('Secondo piatto')
	contorni = ricavaTagsDellaPortata('Contorno')
	dessert = ricavaTagsDellaPortata('Dessert')

	i = 0
	for giorno,ricette in ricetteSettimana.items():
		costo_primi, costo_secondi, costo_contorni,costo_dessert = 0.0,0.0,0.0,0.0
		totPrimi, totSecondi, totContorni,totDessert = 0,0,0,0
		for ricetta in ricette:
			if ricetta.tag in primi:
				costo_primi+= calcolaCostoRicetta(ricetta,impianto)
				totPrimi+=1
			if ricetta.tag in secondi:
				costo_secondi+= calcolaCostoRicetta(ricetta,impianto)
				totSecondi += 1
			if ricetta.tag in contorni:
				costo_contorni+= calcolaCostoRicetta(ricetta,impianto)
				totContorni+=1
			if ricetta.tag in dessert:
				costo_dessert+= calcolaCostoRicetta(ricetta,impianto)
				totDessert+=1
		costo_primi, costo_secondi, costo_contorni,costo_dessert = round(costo_primi,2), round(costo_secondi,2), round(costo_contorni,2),round(costo_dessert,2)
		
		if totPrimi:
			costoTotale[i]+= (costo_primi / totPrimi)
		if totSecondi:
			costoTotale[i]+= (costo_secondi / totSecondi)
		if totContorni:
			costoTotale[i]+= (costo_contorni / totContorni)	
		if totDessert:
			costoTotale[i]+= (costo_dessert / totDessert)		
				
		costoTotale[i] = round(costoTotale[i],2)
		i+=1
	return costoTotale



#Calcola le ricette ORDINATE dei 5 giorni nel menu settimanale di un certo impianto
def getRicetteSettimana(impianto,year,sett,giorni):
	ricetteSettimana= dict()
	for giorno in giorni:
		ricetteSettimana[giorno] = getRicetteGiornoOrdinate(impianto,year,sett,giorno)	
	return ricetteSettimana



#ritorna la lista delle ricette ordinate di un certo giorno
def getRicetteGiornoOrdinate(impianto,year,sett,giorno):
	return MenuSettimana.objects.get(impianto=impianto,anno=year, settimana=sett,giorno=giorno).ricette.order_by('tag')


def approvato(menuSettimana):
	cont = set()
	for menu in menuSettimana:
		cont.add(menu.approvatore)
	if None in cont:
		return False
	if len(cont)==1 and None not in cont:
		return True
	return False



#Data in input la lista dei 5 menu settimanali, ritorna l'istante piu grande delle modifiche
#Se non ci sono modifiche allora ritorna la data di creazione
def getUltimaModifica(menuSettimana):
	ins = set()
	creazione = menuSettimana[0].creazione
	for menu in menuSettimana:
		ha = HistoryMenu.objects.filter(menu=menu).order_by('-istante').first()
		if ha:
			ins.add(ha.istante)
	if ins:
		return max(ins)
	return creazione



def render_to_pdf(template_src, context_dict={}):
	template = get_template(template_src)
	html  = template.render(context_dict)
	result = BytesIO()
	pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
	if not pdf.err:
		return HttpResponse(result.getvalue(), content_type='application/pdf')
	return None





def creaFileExcel(nome_file):
	response = HttpResponse(content_type='application/ms-excel')
	filename = "%s.xls" %(nome_file)
	content = "attachment; filename=%s" %(filename)
	response['Content-Disposition'] = content

	wb = xlwt.Workbook(encoding='utf-8')
	return wb,response


def creaSheetExcel(wb,nome_sheet,columns,rows):
	ws = wb.add_sheet(nome_sheet)
	row_num = 0
	font_style = xlwt.XFStyle()
	font_style.font.bold = True
	for col_num in range(len(columns)):
		ws.write(row_num, col_num, columns[col_num], font_style)
	font_style = xlwt.XFStyle()
	for row in rows:
		row_num += 1
		for col_num in range(len(row)):
			ws.write(row_num, col_num, row[col_num], font_style)
	return wb



def getImpiantiTab(request):
	impiantiTab = dict()
	if request.user.is_staff:
		aree = Area.objects.all()
		for area in aree:
			impiantiTab[area] = Impianto.objects.filter(area=area)
	else:
		try:
			impianto = Chef.objects.get(user = request.user).impianto
			impiantiTab[impianto.area] = [impianto]
		except Chef.DoesNotExist:
			area = Area.objects.get(capo__user = request.user)
			impiantiTab[area] = Impianto.objects.filter(area=area)
	return impiantiTab



def nuovoFornitore(request):
	nome = request.POST.get('nome')
	try:
		Fornitore.objects.get(nome__iexact=nome)
		messages.error(request,"fornitore già esistente nel sistema")
		return None
	except Fornitore.DoesNotExist:
		obj = Fornitore(nome=nome.lower())
		obj.save()
		messages.success(request,"Fornitore '" + obj.nome + "' creato con successo")
		return obj

def eliminaFornitore(request):
	nome = request.POST.get("elimina")
	try:
		f = Fornitore.objects.get(nome__iexact = nome)
		f.delete()
		messages.success(request, "fornitore '" +nome + "' eliminato con successo")
	except Fornitore.DoesNotExist:
		messages.error(request, "Errore, fornitore inesistente")    


def nuovoUtente(request):
	username = request.POST.get('username')
	try:
		User.objects.get(username__iexact=username)
		messages.error(request,"username già esistente nel sistema")
		return None
	except User.DoesNotExist:
		password = request.POST.get('password')
		nome = request.POST.get('nome')
		cognome = request.POST.get('cognome')
		email = request.POST.get('email')
		user = User(username=username,email=email,first_name=nome,last_name=cognome)
		user.set_password(password)
		user.save()
		return user


def nuovoChef(request):
	user = nuovoUtente(request)

	if user != None:
		impianto = Impianto.objects.get(nome= request.POST.get('impianto'))

		chef = Chef(user=user,impianto=impianto) 
		if request.POST.get('manager'):
			Chef.objects.filter(impianto=impianto,manager=True).update(manager=False)
			chef.manager = True
		chef.save()

		messages.success(request,"Utente '" + user.username + "' creato con successo")



def nuovoUtenteDirezionale(request):
	user = nuovoUtente(request)
	if user != None:
		user.is_staff = True
		user.is_superuser = True
		user.save()

		messages.success(request,"Utente '" + user.username + "' creato con successo")




def nuovoCapoArea(request):
	user = nuovoUtente(request)

	if user != None:
		capo = CapoArea(user=user)
		capo.save()

		area = Area.objects.get(nome__iexact= request.POST.get('area'))		
		area.capo = capo
		area.save()

		messages.success(request,"Utente '" + user.username + "' creato con successo")



def eliminaUtente(request):
	username = request.POST.get("elimina")
	try:
		u = User.objects.get(username__iexact = username)
		u.delete()
		messages.success(request, "account '" +username + "' eliminato con successo")
	except User.DoesNotExist:
		messages.error(request, "Errore, utente inesistente")   




def cambiaPassword(request):
	username = request.POST.get("cambia")
	password = request.POST.get('password')
	try:
		u = User.objects.get(username__iexact = username)
		u.set_password(password)
		u.save()
		messages.success(request, "Password cambiata con successo all'account: '" + username + "'")
	except User.DoesNotExist:
		messages.error(request, "Errore, utente inesistente") 


def eliminaRicetta(request):
	nome = request.POST.get("elimina")
	try:
		ricetta = Ricetta.objects.get(nome__iexact = nome)
		if ricetta.foto:
			os.remove(ricetta.foto.path)
		ricetta.delete()
		messages.success(request, "ricetta '" +nome + "' eliminata con successo")
	except User.DoesNotExist:
		messages.error(request, "Errore, ricetta inesistente")  



def ricavaTagsDellaPortata(portata):
	portateAmmesse = Portata.objects.filter().values_list('nome',flat=True)
	if portata.lower() == 'primo piatto':
		tags = Tag.objects.filter( Q(nome__iexact="zuppa") |  Q(nome__iexact="primo classico") |  Q(nome__iexact="primo speciale"))
	elif portata.lower() == 'contorno':
		tags = Tag.objects.filter( Q(nome__iexact="contorno"))
	elif portata.lower() == 'secondo piatto':
		tags = Tag.objects.filter( Q(nome__iexact="secondo di carne rossa") |  Q(nome__iexact="secondo di carne bianca") |  Q(nome__iexact="secondo di pesce") |  Q(nome__iexact="vegetariano") |  Q(nome__iexact="vegano"))
	elif portata.lower() == 'dessert':
		tags = Tag.objects.filter(nome__iexact='dessert')
	elif portata.lower() == 'none':
		tags = Tag.objects.all()
	else:
		tags = []
	return tags