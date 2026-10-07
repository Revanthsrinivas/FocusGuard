print('Testing core functionality...')
from main import FocusGuardPro
app = FocusGuardPro()
app.start()
import time
time.sleep(3)
stats = app.get_stats()
print(f'Focus: {stats["current_focus"]}% | Predictions: {stats["predictions"]} | Accuracy: {stats["model_accuracy"]*100:.0f}%')
app.stop()
print('SUCCESS: Core system working!')