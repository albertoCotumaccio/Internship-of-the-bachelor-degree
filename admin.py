from django.contrib import admin

from .models import Ingrediente, Ricetta, Contenuto, Tag, Allergene, Portata, Area,Impianto,Chef,MenuSettimana, IngredienteImpianto, Fornitore, HistoryMenu, CapoArea


@admin.register(Ingrediente) #è una decorazione
class IngredienteAdmin(admin.ModelAdmin):
	#prepopulated_fields = {'slug': ('title',)}
	list_display = ('nome_generico',)
	search_fields = ('nome_generico',)

@admin.register(Ricetta) #è una decorazione
class RicettaAdmin(admin.ModelAdmin):
	list_display = ('nome','portata','tag','chef','approvata','foto')
	list_filter = ('portata','tag','approvata','chef__impianto')
	search_fields = ('nome',)
	ordering = ('nome',)

@admin.register(Contenuto) #è una decorazione
class ContenutoAdmin(admin.ModelAdmin):
	list_display = ('ricetta','ingrediente','quantita')
	list_filter = ('ricetta__approvata','ricetta__chef__impianto','ricetta__tag','ricetta__portata')
	search_fields = ('ricetta__nome','ingrediente__nome_generico')
	ordering = ('ricetta','-quantita')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
	list_display = ('nome','posizione')
	ordering = ('posizione','nome')


@admin.register(Allergene) #è una decorazione
class AllergeneAdmin(admin.ModelAdmin):
	#prepopulated_fields = {'slug': ('title',)}
	list_display = ('nome','foto')

admin.site.register(Portata)


admin.site.register(CapoArea)



@admin.register(Area) #è una decorazione
class AreaAdmin(admin.ModelAdmin):
	list_display = ('nome','capo')


@admin.register(Impianto) #è una decorazione
class ImpiantoAdmin(admin.ModelAdmin):
	#prepopulated_fields = {'slug': ('title',)}
	list_display = ('nome','area')
	list_filter = ('area',)
	search_fields = ('nome',)
	ordering = ('nome','area')


admin.site.register(Fornitore)

@admin.register(IngredienteImpianto) #è una decorazione
class IngredienteImpiantoAdmin(admin.ModelAdmin):
	list_display = ('ingrediente','impianto','listino','fornitore')
	list_filter = ('impianto',)
	search_fields = ('ingrediente__nome_generico', 'impianto__nome')
	ordering = ('ingrediente__nome_generico','-listino')

@admin.register(Chef) #è una decorazione
class ChefAdmin(admin.ModelAdmin):
	list_display = ('user','impianto','manager')
	list_filter = ('impianto','manager')
	search_fields = ('user__username',)
	ordering = ('impianto__nome','user__username')

@admin.register(MenuSettimana) #è una decorazione
class MenuSettimanaAdmin(admin.ModelAdmin):
	list_display = ('impianto','anno','settimana','giorno','creatore','creazione', 'approvatore')
	list_filter = ('anno','impianto','creazione','giorno')
	search_fields = ('approvatore__username','creatore__username')
	ordering = ('impianto','creazione')


@admin.register(HistoryMenu) #è una decorazione
class HistoryMenuAdmin(admin.ModelAdmin):
	list_display = ('menu','version','text','user', 'istante')
	#list_filter = ('anno','impianto','creazione')
	#search_fields = ('approvatore__username','creatore__username')
	#ordering = ('impianto','creazione')