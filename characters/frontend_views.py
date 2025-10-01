"""
Frontend Views for Character Creation

These views serve the HTML templates for the character creation process.
They work with HTMX for dynamic content loading and Alpine.js for interactivity.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView
from django.db.models import Q

from .models import Character
from game_content.models import DnDClass, Species, Background, Equipment, Spell, Skill
from .services import CharacterCalculationService, CharacterValidationService, RecommendationService


class CharacterListView(LoginRequiredMixin, ListView):
    """
    Display list of user's characters
    """
    model = Character
    template_name = 'pages/character_list.html'
    context_object_name = 'characters'
    paginate_by = 12

    def get_queryset(self):
        queryset = Character.objects.filter(
            user=self.request.user
        ).select_related(
            'dnd_class', 'species', 'background', 'abilities'
        ).order_by('-updated_at', '-created_at')

        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(character_name__icontains=search) |
                Q(dnd_class__name__icontains=search) |
                Q(species__name__icontains=search) |
                Q(background__name__icontains=search)
            )

        # Filter functionality
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(is_complete=(status == 'complete'))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


@login_required
def character_create_wizard(request, character_id=None):
    """
    Main character creation wizard entry point
    """
    # Get or create character
    if character_id:
        character = get_object_or_404(Character, id=character_id, user=request.user)
    else:
        # Create a new draft character
        character = Character.objects.create(
            user=request.user,
            character_name="New Character",
            level=1,
            is_complete=False
        )
        return redirect('character_create_step', character_id=character.id, step=1)

    # Redirect to appropriate step
    current_step = determine_current_step(character)
    return redirect('character_create_step', character_id=character.id, step=current_step)


@login_required
def character_create_step(request, character_id, step):
    """
    Handle individual steps of character creation
    """
    character = get_object_or_404(Character, id=character_id, user=request.user)
    step = int(step)

    if request.method == 'POST':
        return handle_step_submission(request, character, step)

    # Prepare step data
    context = get_step_context(character, step)
    context.update({
        'character': character,
        'current_step': step,
        'steps': get_wizard_steps(),
        'progress_percentage': calculate_progress_percentage(character, step),
    })

    # Return appropriate template based on step
    template_mapping = {
        1: 'pages/step1_class.html',
        2: 'pages/step2_origin.html',
        3: 'pages/step3_abilities.html',
        4: 'pages/step4_alignment.html',
        5: 'pages/step5_equipment.html',
        6: 'pages/step6_details.html',
    }

    template = template_mapping.get(step, 'pages/step1_class.html')

    # For HTMX requests, return just the content
    if request.headers.get('HX-Request'):
        return render(request, template, context)

    # For full page requests, return with base template
    context['base_template'] = 'base/character_wizard.html'
    return render(request, template, context)


@require_http_methods(["POST"])
@login_required
def character_save_draft(request, character_id):
    """
    Save character as draft via AJAX
    """
    try:
        character = get_object_or_404(Character, id=character_id, user=request.user)

        # Process form data and save
        # This would be implemented based on the specific step data
        character.save()

        return JsonResponse({'success': True, 'message': 'Draft saved successfully'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def character_delete(request, character_id):
    """
    Delete a character
    """
    character = get_object_or_404(Character, id=character_id, user=request.user)

    if request.method == 'POST':
        character_name = character.character_name
        character.delete()
        messages.success(request, f'Character "{character_name}" deleted successfully.')
        return redirect('character_list')

    return render(request, 'pages/character_delete_confirm.html', {
        'character': character
    })


@login_required
def character_duplicate(request, character_id):
    """
    Duplicate an existing character
    """
    original = get_object_or_404(Character, id=character_id, user=request.user)

    if request.method == 'POST':
        # Create a copy
        duplicate = Character.objects.get(id=original.id)
        duplicate.pk = None  # This will create a new instance when saved
        duplicate.character_name = f"{original.character_name} (Copy)"
        duplicate.is_complete = False
        duplicate.save()

        # Copy related objects if they exist
        if hasattr(original, 'abilities'):
            abilities = original.abilities
            abilities.pk = None
            abilities.character = duplicate
            abilities.save()

        # Copy other relationships as needed...

        messages.success(request, f'Character duplicated as "{duplicate.character_name}"')
        return redirect('character_create_step', character_id=duplicate.id, step=1)

    return render(request, 'pages/character_duplicate_confirm.html', {
        'character': original
    })


def character_sheet_view(request, character_id):
    """
    Display complete character sheet
    """
    character = get_object_or_404(
        Character.objects.select_related(
            'dnd_class', 'species', 'background', 'abilities'
        ).prefetch_related(
            'skills', 'equipment', 'spells', 'feats'
        ),
        id=character_id
    )

    # Check permissions - owner or public character
    if character.user != request.user and not getattr(character, 'is_public', False):
        messages.error(request, "You don't have permission to view this character.")
        return redirect('character_list')

    # Calculate all character stats
    if hasattr(character, 'abilities'):
        stats = CharacterCalculationService.calculate_all_stats(character)
    else:
        stats = {}

    context = {
        'character': character,
        'stats': stats,
        'is_owner': character.user == request.user,
    }

    return render(request, 'pages/character_sheet.html', context)


# Helper Functions

def determine_current_step(character):
    """
    Determine which step the character should be on based on completion status
    """
    if not character.dnd_class:
        return 1
    if not character.species or not character.background:
        return 2
    if not hasattr(character, 'abilities'):
        return 3
    if not character.alignment:
        return 4
    if not character.equipment.exists():
        return 5
    if not character.character_name or character.character_name == "New Character":
        return 6
    return 6  # All steps complete


def get_wizard_steps():
    """
    Return list of wizard steps with metadata
    """
    return [
        {
            'number': 1,
            'title': 'Class',
            'subtitle': 'Choose your class',
            'url_name': 'character_create_step'
        },
        {
            'number': 2,
            'title': 'Origin',
            'subtitle': 'Background & species',
            'url_name': 'character_create_step'
        },
        {
            'number': 3,
            'title': 'Abilities',
            'subtitle': 'Set ability scores',
            'url_name': 'character_create_step'
        },
        {
            'number': 4,
            'title': 'Alignment',
            'subtitle': 'Moral compass',
            'url_name': 'character_create_step'
        },
        {
            'number': 5,
            'title': 'Equipment',
            'subtitle': 'Gear & spells',
            'url_name': 'character_create_step'
        },
        {
            'number': 6,
            'title': 'Details',
            'subtitle': 'Name & backstory',
            'url_name': 'character_create_step'
        },
    ]


def calculate_progress_percentage(character, current_step):
    """
    Calculate overall completion percentage
    """
    completed_steps = current_step - 1
    return int((completed_steps / 6) * 100)


def get_step_context(character, step):
    """
    Get context data specific to each step
    """
    context = {}

    if step == 1:
        # Class selection
        context['classes'] = DnDClass.objects.all().order_by('name')
        context['selected_class'] = character.dnd_class

        # Get class recommendations if user is new
        if not character.dnd_class and character.user.characters.count() == 1:
            # This is their first character, show recommendations
            context['show_recommendations'] = True

    elif step == 2:
        # Origin (Background & Species)
        context['species'] = Species.objects.all().order_by('name')
        context['backgrounds'] = Background.objects.all().order_by('name')
        context['selected_species'] = character.species
        context['selected_background'] = character.background

        # Show synergy recommendations if class is selected
        if character.dnd_class:
            context['recommended_species'] = RecommendationService.recommend_species_for_class(
                character.dnd_class.name
            )
            context['recommended_backgrounds'] = RecommendationService.recommend_background_for_class(
                character.dnd_class.name
            )

    elif step == 3:
        # Ability Scores
        context['abilities'] = getattr(character, 'abilities', None)

        # Ability score recommendations for the class
        if character.dnd_class:
            context['ability_priorities'] = RecommendationService.recommend_ability_score_priority(
                character.dnd_class.name
            )

    elif step == 4:
        # Alignment
        context['alignments'] = [
            ('LG', 'Lawful Good'), ('NG', 'Neutral Good'), ('CG', 'Chaotic Good'),
            ('LN', 'Lawful Neutral'), ('TN', 'True Neutral'), ('CN', 'Chaotic Neutral'),
            ('LE', 'Lawful Evil'), ('NE', 'Neutral Evil'), ('CE', 'Chaotic Evil'),
        ]
        context['selected_alignment'] = character.alignment

    elif step == 5:
        # Equipment & Spells
        context['equipment'] = Equipment.objects.all()
        context['character_equipment'] = character.equipment.all()

        if character.dnd_class and getattr(character.dnd_class, 'spellcaster', False):
            context['spells'] = Spell.objects.filter(
                available_to_classes=character.dnd_class,
                spell_level__lte=1  # Level 1 character spells
            )
            context['character_spells'] = character.spells.all()

    elif step == 6:
        # Character Details
        context['character_details'] = getattr(character, 'details', None)

    return context


def handle_step_submission(request, character, step):
    """
    Handle form submission for each step
    """
    if step == 1:
        # Handle class selection
        class_id = request.POST.get('class_id')
        if class_id:
            try:
                dnd_class = DnDClass.objects.get(id=class_id)
                character.dnd_class = dnd_class
                character.save()
                messages.success(request, f'Class "{dnd_class.name}" selected!')
            except DnDClass.DoesNotExist:
                messages.error(request, 'Invalid class selected.')

    elif step == 2:
        # Handle origin selection
        species_id = request.POST.get('species_id')
        background_id = request.POST.get('background_id')

        if species_id:
            try:
                species = Species.objects.get(id=species_id)
                character.species = species
            except Species.DoesNotExist:
                messages.error(request, 'Invalid species selected.')

        if background_id:
            try:
                background = Background.objects.get(id=background_id)
                character.background = background
            except Background.DoesNotExist:
                messages.error(request, 'Invalid background selected.')

        character.save()

    # Continue for other steps...

    # Redirect to next step or finish
    if step < 6:
        return redirect('character_create_step', character_id=character.id, step=step + 1)
    else:
        # Final step - mark character as complete
        character.is_complete = True
        character.save()
        messages.success(request, f'Character "{character.character_name}" created successfully!')
        return redirect('character_sheet', character_id=character.id)