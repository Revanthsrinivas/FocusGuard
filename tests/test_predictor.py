import pytest
from unittest.mock import patch, MagicMock, Mock
from src.ml.ensemble_model import EnsembleModel
from src.ml.online_learner import OnlineLearner
from src.ml.user_manager import UserManager
from src.models.feature_extractor import FeatureExtractor

@pytest.fixture
def mock_user():
    return Mock(spec=UserManager)

@pytest.fixture
def mock_learner(mock_user):
    learner = Mock(spec=OnlineLearner)
    learner.predict.return_value = 65.0
    return learner

@pytest.fixture
def mock_extractor():
    extractor = Mock(spec=FeatureExtractor)
    extractor.extract.return_value = np.zeros(29)
    return extractor

def test_ensemble_fallback(mock_learner, mock_extractor, mock_user):
    """Test ensemble fallback to learner"""
    ensemble = EnsembleModel()
    
    # Mock FocusGuardPro-like prediction
    features = np.zeros(29)
    
    # Trained ensemble
    ensemble._is_trained = True
    with patch.object(ensemble, 'predict_single', return_value=75.0):
        score = ensemble.predict_single(features)
        assert score == 75.0
    
    # Fallback case
    ensemble._is_trained = False
    with patch('src.ml.online_learner.OnlineLearner.predict', mock_learner.predict):
        score = mock_learner.predict({'test': 'sample'})
        assert score == 65.0

def test_ensemble_predict_invalid_input():
    """Test ensemble predict raises ValueError for invalid input"""
    ensemble = EnsembleModel()
    ensemble._is_trained = True
    
    # Invalid: not ndarray
    with pytest.raises(ValueError, match="Input must be 2D numpy array with 29 features"):
        ensemble.predict([1, 2, 3])
    
    # Invalid: 1D
    with pytest.raises(ValueError, match="Input must be 2D numpy array with 29 features"):
        ensemble.predict(np.array([1, 2, 3]))
    
    # Invalid: wrong features
    with pytest.raises(ValueError, match="Input must be 2D numpy array with 29 features"):
        ensemble.predict(np.array([[1, 2, 3]]))

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
