"""
Model Registry - Central registration and management system for all ML models

Provides factory pattern for creating and managing 25+ models.
"""

from typing import Dict, List, Optional
from ml_system.core.base_predictor import BasePredictor


class ModelRegistry:
    """
    Central registry for all ML models in the system.

    Manages models by groups:
    - legacy: 5 existing models (RandomForest, GradientBoosting, Ridge, Lasso, DecisionTree)
    - automl: 16 simulated AutoML models
    - trained: 4 real trained models (RF, GB, LGBM, LSTM)
    - classifiers: 4 binary classifiers (1.5x, 2.0x, 3.0x, 5.0x)
    """

    def __init__(self):
        self.models: Dict[str, BasePredictor] = {}
        self.groups: Dict[str, List[str]] = {
            'legacy': [],
            'automl': [],
            'trained': [],
            'classifiers': []
        }

    def register(self, name: str, model: BasePredictor, group: str):
        """
        Register a model with the system.

        Args:
            name: Unique model name
            model: BasePredictor instance
            group: Group category (legacy, automl, trained, classifiers)
        """
        if name in self.models:
            print(f"[WARNING] Model '{name}' already registered, overwriting")

        self.models[name] = model

        if group in self.groups:
            if name not in self.groups[group]:
                self.groups[group].append(name)
        else:
            print(f"[WARNING] Unknown group '{group}', creating new group")
            self.groups[group] = [name]

    def get_model(self, name: str) -> Optional[BasePredictor]:
        """Get a specific model by name."""
        return self.models.get(name)

    def get_group(self, group: str) -> List[BasePredictor]:
        """Get all models in a specific group."""
        model_names = self.groups.get(group, [])
        return [self.models[name] for name in model_names if name in self.models]

    def get_all_models(self) -> List[BasePredictor]:
        """Get all registered models."""
        return list(self.models.values())

    def get_trained_models(self) -> List[BasePredictor]:
        """Get all models that have been trained."""
        return [model for model in self.models.values() if model.is_trained]

    def get_model_count(self) -> int:
        """Get total number of registered models."""
        return len(self.models)

    def get_group_counts(self) -> Dict[str, int]:
        """Get count of models in each group."""
        return {group: len(names) for group, names in self.groups.items()}

    def __repr__(self) -> str:
        counts = self.get_group_counts()
        return f"ModelRegistry(total={self.get_model_count()}, legacy={counts.get('legacy', 0)}, automl={counts.get('automl', 0)}, trained={counts.get('trained', 0)}, classifiers={counts.get('classifiers', 0)})"


class ModelFactory:
    """
    Factory for creating and registering all models.

    Handles the initialization of all 25+ models and registration
    with the ModelRegistry.
    """

    @staticmethod
    def create_all_models(registry: ModelRegistry, feature_extractor, feature_adapter=None):
        """
        Create and register all 25+ models.

        Args:
            registry: ModelRegistry instance
            feature_extractor: FeatureExtractor instance
            feature_adapter: FeatureAdapter instance (optional, for trained models)

        Returns:
            None (models are registered in the registry)
        """
        from datetime import datetime

        print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Initializing ML models...")

        # Group 1: Legacy models (5) - DISABLED
        # try:
        #     from ml_system.models.legacy_models import create_legacy_models
        #     legacy_models = create_legacy_models(feature_extractor)
        #     for model in legacy_models:
        #         registry.register(model.name, model, 'legacy')
        #     print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Registered {len(legacy_models)} legacy models")
        # except Exception as e:
        #     print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Failed to load legacy models: {e}")

        # Group 2: AutoML models (16)
        try:
            from ml_system.models.automl_models import create_automl_models
            automl_models = create_automl_models(feature_extractor)
            for model in automl_models:
                registry.register(model.name, model, 'automl')
            print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Registered {len(automl_models)} AutoML models")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Failed to load AutoML models: {e}")

        # Group 3: Trained models (4) - DISABLED
        # if feature_adapter:
        #     try:
        #         from ml_system.models.trained_models import create_trained_models
        #         trained_models = create_trained_models(feature_extractor, feature_adapter)
        #         for model in trained_models:
        #             registry.register(model.name, model, 'trained')
        #         print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Registered {len(trained_models)} trained models")
        #     except Exception as e:
        #         print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Failed to load trained models: {e}")
        # else:
        #     print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Skipping trained models (no feature adapter)")

        # Group 4: Binary classifiers (4) - DISABLED
        # try:
        #     from ml_system.models.binary_classifiers import create_binary_classifiers
        #     classifiers = create_binary_classifiers(feature_extractor)
        #     for classifier in classifiers:
        #         registry.register(classifier.name, classifier, 'classifiers')
        #     print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Registered {len(classifiers)} binary classifiers")
        # except Exception as e:
        #     print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Failed to load binary classifiers: {e}")

        counts = registry.get_group_counts()
        total = registry.get_model_count()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Total models registered: {total}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: Breakdown - Legacy: {counts.get('legacy', 0)}, AutoML: {counts.get('automl', 0)}, Trained: {counts.get('trained', 0)}, Classifiers: {counts.get('classifiers', 0)}")
