/**
 * D&D Character Creator - Main JavaScript
 *
 * This file contains Alpine.js components and HTMX integrations
 * for the character creation process.
 */

// Global utilities
window.DnDApp = {
    // API endpoints
    api: {
        roll: '/api/utility/dice/roll/',
        rollAbilityScores: '/api/utility/dice/ability-scores/',
        rollAdvantage: '/api/utility/dice/advantage/',
        validateCharacter: '/api/utility/validate/character/',
        recommendations: '/api/utility/recommendations/classes/',
        buildRecommendations: '/api/utility/recommendations/build/',
        analyzeCharacter: '/api/utility/analyze/character/',
        generateName: '/api/utility/generate/name/',
        characters: '/api/characters/',
        classes: '/api/classes/',
        species: '/api/species/',
        backgrounds: '/api/backgrounds/',
        equipment: '/api/equipment/',
        spells: '/api/spells/',
    },

    // Utility functions
    utils: {
        // Format dice notation
        formatDice(count, sides, modifier = 0) {
            let notation = `${count}d${sides}`;
            if (modifier > 0) notation += `+${modifier}`;
            if (modifier < 0) notation += modifier;
            return notation;
        },

        // Calculate ability modifier
        abilityModifier(score) {
            return Math.floor((score - 10) / 2);
        },

        // Format modifier with sign
        formatModifier(modifier) {
            return modifier >= 0 ? `+${modifier}` : `${modifier}`;
        },

        // Debounce function for auto-save
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        // Show toast notification
        showToast(message, type = 'info') {
            // Create toast element
            const toast = document.createElement('div');
            toast.className = `fixed top-4 right-4 z-50 px-4 py-2 rounded-md shadow-lg transition-all duration-300 transform translate-x-full`;

            // Set toast type styling
            switch (type) {
                case 'success':
                    toast.className += ' bg-green-600 text-white';
                    break;
                case 'error':
                    toast.className += ' bg-red-600 text-white';
                    break;
                case 'warning':
                    toast.className += ' bg-yellow-600 text-black';
                    break;
                default:
                    toast.className += ' bg-blue-600 text-white';
            }

            toast.textContent = message;
            document.body.appendChild(toast);

            // Animate in
            setTimeout(() => {
                toast.classList.remove('translate-x-full');
            }, 100);

            // Remove after delay
            setTimeout(() => {
                toast.classList.add('translate-x-full');
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.parentNode.removeChild(toast);
                    }
                }, 300);
            }, 3000);
        },

        // Get CSRF token
        getCsrfToken() {
            return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        },

        // Make authenticated API request
        async apiRequest(url, options = {}) {
            const defaults = {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                },
                credentials: 'same-origin',
            };

            const config = { ...defaults, ...options };
            if (config.headers) {
                config.headers = { ...defaults.headers, ...options.headers };
            }

            try {
                const response = await fetch(url, config);
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || `HTTP ${response.status}`);
                }

                return data;
            } catch (error) {
                console.error('API Request failed:', error);
                this.showToast(`Error: ${error.message}`, 'error');
                throw error;
            }
        }
    },

    // Character creation state
    characterState: Alpine.reactive({
        currentStep: 1,
        characterId: null,
        characterData: {
            name: '',
            class: null,
            species: null,
            background: null,
            abilityScores: {
                strength: 10,
                dexterity: 10,
                constitution: 10,
                intelligence: 10,
                wisdom: 10,
                charisma: 10
            },
            alignment: null,
            equipment: [],
            spells: [],
            details: {}
        },

        // Auto-save functionality
        autoSave: null,

        init() {
            // Set up auto-save
            this.autoSave = DnDApp.utils.debounce(() => {
                this.saveCharacter();
            }, 2000);

            // Watch for changes
            this.$watch('characterData', () => {
                this.autoSave();
            });
        },

        async saveCharacter() {
            if (!this.characterId) return;

            try {
                await DnDApp.utils.apiRequest(`${DnDApp.api.characters}${this.characterId}/`, {
                    method: 'PATCH',
                    body: JSON.stringify(this.characterData)
                });

                DnDApp.utils.showToast('Character saved', 'success');
            } catch (error) {
                console.error('Failed to save character:', error);
            }
        },

        nextStep() {
            if (this.currentStep < 6) {
                this.currentStep++;
            }
        },

        previousStep() {
            if (this.currentStep > 1) {
                this.currentStep--;
            }
        },

        goToStep(step) {
            if (step >= 1 && step <= 6) {
                this.currentStep = step;
            }
        }
    })
};

// Alpine.js Components
document.addEventListener('alpine:init', () => {

    // Dice Roller Component
    Alpine.data('diceRoller', () => ({
        notation: '1d20',
        result: null,
        isRolling: false,

        async roll() {
            if (this.isRolling) return;

            this.isRolling = true;
            this.result = null;

            try {
                const data = await DnDApp.utils.apiRequest(DnDApp.api.roll, {
                    method: 'POST',
                    body: JSON.stringify({ notation: this.notation })
                });

                this.result = data;

                // Add animation delay
                setTimeout(() => {
                    this.isRolling = false;
                }, 500);
            } catch (error) {
                this.isRolling = false;
            }
        },

        get diceColor() {
            const sides = this.result?.dice_size || 20;
            const colors = {
                4: 'dice-d4',
                6: 'dice-d6',
                8: 'dice-d8',
                10: 'dice-d10',
                12: 'dice-d12',
                20: 'dice-d20'
            };
            return colors[sides] || 'dice-d20';
        }
    }));

    // Ability Score Generator Component
    Alpine.data('abilityScoreGenerator', () => ({
        method: 'standard_array',
        scores: null,
        isRolling: false,
        standardArray: [15, 14, 13, 12, 10, 8],
        pointBuyScores: {
            strength: 8,
            dexterity: 8,
            constitution: 8,
            intelligence: 8,
            wisdom: 8,
            charisma: 8
        },
        pointsUsed: 0,
        maxPoints: 27,

        init() {
            this.loadMethod();
        },

        loadMethod() {
            switch (this.method) {
                case 'standard_array':
                    this.loadStandardArray();
                    break;
                case 'point_buy':
                    this.loadPointBuy();
                    break;
                case 'roll':
                    // Keep existing rolled scores if any
                    break;
            }
        },

        loadStandardArray() {
            this.scores = {
                strength: { total: 15, assigned: false },
                dexterity: { total: 14, assigned: false },
                constitution: { total: 13, assigned: false },
                intelligence: { total: 12, assigned: false },
                wisdom: { total: 10, assigned: false },
                charisma: { total: 8, assigned: false }
            };
        },

        loadPointBuy() {
            this.calculatePointBuy();
        },

        calculatePointBuy() {
            const costs = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9};
            let total = 0;

            Object.values(this.pointBuyScores).forEach(score => {
                total += costs[score] || 0;
            });

            this.pointsUsed = total;

            // Update scores object
            this.scores = {};
            Object.keys(this.pointBuyScores).forEach(ability => {
                this.scores[ability] = {
                    total: this.pointBuyScores[ability],
                    assigned: true
                };
            });
        },

        async rollScores() {
            this.isRolling = true;

            try {
                const data = await DnDApp.utils.apiRequest(DnDApp.api.rollAbilityScores, {
                    method: 'POST',
                    body: JSON.stringify({})
                });

                this.scores = {};
                Object.keys(data.scores).forEach(ability => {
                    this.scores[ability] = {
                        rolls: data.scores[ability].rolls,
                        total: data.scores[ability].total,
                        assigned: true
                    };
                });

                setTimeout(() => {
                    this.isRolling = false;
                }, 1000);
            } catch (error) {
                this.isRolling = false;
            }
        },

        adjustPointBuy(ability, change) {
            const newScore = this.pointBuyScores[ability] + change;
            if (newScore < 8 || newScore > 15) return;

            const costs = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9};
            const currentCost = costs[this.pointBuyScores[ability]];
            const newCost = costs[newScore];
            const costDiff = newCost - currentCost;

            if (this.pointsUsed + costDiff <= this.maxPoints) {
                this.pointBuyScores[ability] = newScore;
                this.calculatePointBuy();
            }
        },

        get remainingPoints() {
            return this.maxPoints - this.pointsUsed;
        },

        abilityModifier(score) {
            return DnDApp.utils.abilityModifier(score);
        }
    }));

    // Character Creation Wizard Component
    Alpine.data('characterWizard', (characterId = null) => ({
        ...DnDApp.characterState,
        characterId,

        init() {
            if (this.characterId) {
                this.loadCharacter();
            }
            DnDApp.characterState.init.call(this);
        },

        async loadCharacter() {
            try {
                const data = await DnDApp.utils.apiRequest(`${DnDApp.api.characters}${this.characterId}/`);
                this.characterData = { ...this.characterData, ...data };
            } catch (error) {
                console.error('Failed to load character:', error);
            }
        },

        async saveAndContinue() {
            try {
                if (!this.characterId) {
                    // Create new character
                    const data = await DnDApp.utils.apiRequest(DnDApp.api.characters, {
                        method: 'POST',
                        body: JSON.stringify(this.characterData)
                    });
                    this.characterId = data.id;
                    DnDApp.utils.showToast('Character created', 'success');
                } else {
                    // Update existing character
                    await this.saveCharacter();
                }

                this.nextStep();
            } catch (error) {
                console.error('Failed to save character:', error);
            }
        },

        get stepTitle() {
            const titles = {
                1: 'Choose Your Class',
                2: 'Select Origin',
                3: 'Determine Ability Scores',
                4: 'Choose Alignment',
                5: 'Equipment & Spells',
                6: 'Character Details'
            };
            return titles[this.currentStep] || '';
        },

        get isLastStep() {
            return this.currentStep === 6;
        }
    }));

    // Tooltip Component
    Alpine.data('tooltip', (content) => ({
        content,
        show: false,
        x: 0,
        y: 0,

        showTooltip(event) {
            this.x = event.pageX + 10;
            this.y = event.pageY + 10;
            this.show = true;
        },

        hideTooltip() {
            this.show = false;
        }
    }));

    // Search/Filter Component
    Alpine.data('searchFilter', () => ({
        query: '',
        results: [],
        isLoading: false,

        search(items, searchFields = ['name']) {
            if (!this.query.trim()) {
                this.results = items;
                return;
            }

            const query = this.query.toLowerCase();
            this.results = items.filter(item => {
                return searchFields.some(field => {
                    const value = item[field];
                    return value && value.toLowerCase().includes(query);
                });
            });
        }
    }));

});

// HTMX Event Handlers
document.addEventListener('DOMContentLoaded', function() {
    // Global HTMX error handler
    document.body.addEventListener('htmx:responseError', function(evt) {
        console.error('HTMX Error:', evt.detail);
        DnDApp.utils.showToast('Something went wrong. Please try again.', 'error');
    });

    // Loading indicators
    document.body.addEventListener('htmx:beforeRequest', function(evt) {
        const target = evt.target;
        if (target.classList.contains('loading-trigger')) {
            target.classList.add('opacity-50', 'pointer-events-none');
            const spinner = target.querySelector('.loading-spinner');
            if (spinner) spinner.classList.remove('hidden');
        }
    });

    document.body.addEventListener('htmx:afterRequest', function(evt) {
        const target = evt.target;
        if (target.classList.contains('loading-trigger')) {
            target.classList.remove('opacity-50', 'pointer-events-none');
            const spinner = target.querySelector('.loading-spinner');
            if (spinner) spinner.classList.add('hidden');
        }
    });

    // Auto-focus first input in swapped content
    document.body.addEventListener('htmx:afterSwap', function(evt) {
        const firstInput = evt.detail.target.querySelector('input, select, textarea');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    });
});

// Utility functions for templates
window.formatModifier = DnDApp.utils.formatModifier;
window.abilityModifier = DnDApp.utils.abilityModifier;