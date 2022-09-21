from django.shortcuts import render
from .forms import CsvModelForm
from .models import Csv
import csv
from app.models import Ingrediente, Ricetta, Contenuto, Portata, Tag, Allergene, Fornitore
#from django.http import HttpResponse



#codice per caricare fornitori
def upload_file_view(request):
	form = CsvModelForm(request.POST or None, request.FILES or None)
	if form.is_valid():
		form.save()
		form = CsvModelForm()
		obj = Csv.objects.get(activated=False)
		with open(obj.file_name.path, 'r') as f:
			reader = csv.reader(f)

			allergeniDiz = dict()
			for i,row in enumerate(reader):
				nome= row[0].lower()
				fo = Fornitore()
				fo.nome = nome
				fo.save()
				
			obj.activated = True
			obj.save()
	return render(request, 'csvs/base.html', {'form':form})


"""
#codice per caricare gli allergeni
def upload_file_view(request):
	form = CsvModelForm(request.POST or None, request.FILES or None)
	if form.is_valid():
		form.save()
		form = CsvModelForm()
		obj = Csv.objects.get(activated=False)
		with open(obj.file_name.path, 'r') as f:
			reader = csv.reader(f)

			allergeniDiz = dict()
			for i,row in enumerate(reader):
				if i==0:
					continue

				nome= row[1].lower()
				allergeni = row[3]
				if allergeni != "":
					allergeniDiz[nome] = allergeni.split(";")

			nuovoDiz = dict()
			for key,lista in allergeniDiz.items():
				if key == "biscotti per l'infanzia":
					key = "biscotti per infanzia"
				if key == "biscotti 'petit beurre'":
					key = "biscotti petit beurre"
				if key == "baccalã  ammollato":
					key = "baccalà ammollato"
				if key == "baccalã  secco":
					key = "baccalà secco"

				lista2=[]
				for stringa in lista:
					nuova= " ".join(stringa.split())
					if nuova == "altro":
						nuova = "Altro"
					if nuova == "uova":
						nuova = "Uova"
					if nuova == "latte":
						nuova = "Latte"
					if nuova == "crostacei":
						nuova = "Crostacei"
					if nuova == "molluschi":
						nuova = "Molluschi"
					if nuova == "glutine":
						nuova = "Glutine"
					if nuova == "mozzarella":
						nuova = "Mozzarella"
					if nuova == "Anidride solforosa e solfiti secondo la tipologia":
						nuova = 'Anidride solforosa e solfiti'
					if nuova != "":
						lista2.append(nuova)
				nuovoDiz[key] = lista2
			
			for key,lista in nuovoDiz.items():
				ingObj = Ingrediente.objects.get(nome_generico=key)
				for allergene in lista:
					allObj = Allergene.objects.get(nome=allergene)
					ingObj.allergeni.add(allObj)
					print(allergene + " aggiunto con successo a " + key)
				ingObj.save()




			obj.activated = True
			obj.save()
	return render(request, 'csvs/base.html', {'form':form})
"""


"""

#codice per caricare le ricette
def upload_file_view(request):
	form = CsvModelForm(request.POST or None, request.FILES or None)
	if form.is_valid():
		form.save()
		form = CsvModelForm()
		obj = Csv.objects.get(activated=False)
		with open(obj.file_name.path, 'r') as f:
			reader = csv.reader(f)

			ingredientiDiz = dict()
			tagDiz = dict()
			portateDiz = dict()
			for i,row in enumerate(reader):
				if i==0:
					continue

				tags = ["Primo Speciale", "Carne_bianca", "Carne_rossa", "Pesce", "Primo Classico", "Zuppa", "Vegano", "Vegetariano", "Contorni"]
				portat = ["Primi_piatti", "Secondi_piatti", "Contorni"]

			
				if row[0] not in portat:
					print("Errore portata: "+ str(i) +" "+ row[0])
					continue

				if row[1] not in tags:
					print("Errore tag: "+ str(i) + " "+ row[1])
					continue
				

				if row[2].lower() not in ingredientiDiz.keys():
					portata,tag,nome = row[0], row[1], row[2].lower()
					ingredientiDiz[nome] = [ [row[3], float(row[4]) ] ]
					if portata == "Primi_piatti":
						portateDiz[nome] = "Primo piatto"
					if portata == "Secondi_piatti":
						portateDiz[nome] = "Secondo piatto"
					if portata == "Contorni":
						portateDiz[nome] = "Contorno"
					if tag == "Primo Speciale":
						tagDiz[nome] = "Primo speciale"
					if tag == "Carne_bianca":
						tagDiz[nome] = "Secondo di carne bianca"
					if tag == "Carne_rossa":
						tagDiz[nome] = "Secondo di carne rossa"
					if tag == "Pesce":
						tagDiz[nome] = "Secondo di pesce"
					if tag == "Primo Classico":
						tagDiz[nome] = "Primo classico"
					if tag == "Zuppa":
						tagDiz[nome] = "Zuppa"
					if tag == "Vegano":
						tagDiz[nome] = "Vegano"
					if tag == "Vegetariano":
						tagDiz[nome] = "Vegetariano"
					if tag == "Contorni":
						tagDiz[nome] = "Contorno"
					if tag == "#N/A":
						tagDiz[nome] = "Zuppa"
					continue

				if row[2].lower() in ingredientiDiz.keys():
					insieme = set()
					lista = ingredientiDiz[row[2].lower()]
					for coppia in lista:
						insieme.add(coppia[0])
					if row[3] not in insieme:
						ingredientiDiz[row[2].lower()].append([row[3], float(row[4])])
					if row[3] in insieme:
						for coppia in ingredientiDiz.items():
							if coppia[0] == row[3]:
								coppia[1]+=float(row[4])
								print("qui",coppia[1])

				if row[2].lower() == "pizza margherita homemade":
					print(i)
		
				#print(i,row[2])
			
			for nome,lista in ingredientiDiz.items():
				tagObj = Tag.objects.get(nome=tagDiz[nome])
				portataObj = Portata.objects.get(nome=portateDiz[nome])
				ricetta = Ricetta.objects.create(nome=nome, tag=tagObj, portata=portataObj)
				ricetta.save()
				for coppia in lista:
					ingrediente = str(coppia[0]).lower()
					quantita = coppia[1]
					if ingrediente == "asparago verde":
						ingrediente = "asparago verde di bosco"
					if ingrediente == "panna da cucina":
						ingrediente = "panna da cucina 1"
					
					try:
						ingredienteObj = Ingrediente.objects.get(nome_generico=ingrediente)
					except Ingrediente.DoesNotExist:
						print('Ingrediente '+ ingrediente + 'non trovato per la ricetta '+nome)
						continue

					try:
						contenuto = Contenuto.objects.create(ingrediente=ingredienteObj, quantita=quantita, ricetta=ricetta)
						contenuto.save()
					except:
						print("problemi con "+ ingrediente + 'per la ricetta '+ nome)
						continue
				
			obj.activated = True
			obj.save()
	return render(request, 'csvs/base.html', {'form':form})



#codice per caricare gli ingredienti
def upload_file_view(request):
	form = CsvModelForm(request.POST or None, request.FILES or None)
	if form.is_valid():
		form.save()
		form = CsvModelForm()
		obj = Csv.objects.get(activated=False)
		with open(obj.file_name.path, 'r') as f:
			reader = csv.reader(f)

			for i,row in enumerate(reader):
				if i == 0:
					continue
				row = "".join(row)
				row = row.split(";")
				nome_specifico = row[0].lower()
				nome_generico = row[1]

				
				Ingrediente.objects.create(
					nome_specifico = nome_specifico,
					nome_generico = nome_generico,
					listino = float(row[2]),
					energiaKcal = float(row[3]),
					acqua = float(row[4]),
					protAnim = float(row[5]),
					protVeg = float(row[6]),
					amido = float(row[7]),
					glucidiSolub = float(row[8]),
					saturi = float(row[9]),
					monoins = float(row[10]),
					polins = float(row[11]),
					acidoOleico = float(row[12]),
					acidoLinoleico = float(row[13]),
					acidoLinolenico = float(row[14]),
					altriPolins = float(row[15]),
					colesterolo = float(row[16]),
					fibreAnim = float(row[17]),
					alcool = float(row[18]),
					ferro = float(row[19]),
					ca = float(row[20]),
					na = float(row[21]),
					k = float(row[22]),
					p = float(row[23]),
					zn = float(row[24]),
					vitB1 = float(row[25]),
					vitB2 = float(row[26]),
					vitB3 = float(row[27]),
					vitC = float(row[28]),
					vitB6 = float(row[29]),
					folico = float(row[30]),
					retinolo = float(row[31]),
					betaCarotene = float(row[32]),
					vitE = float(row[33]),
					vitD = float(row[34]),
					parteEdibile = float(row[35]),
					protTot = float(row[5]) + float(row[6]),
					energiaKj = float(row[3])* 4.184,
					glucidiTot = float(row[7]) + float(row[8]),
					lipidiTot = float(row[9]) + float(row[10]) + float(row[11]) + float(row[15]),
			)

			obj.activated = True
			obj.save()
	return render(request, 'csvs/base.html', {'form':form})

"""