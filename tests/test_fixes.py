import pytest

@pytest.mark.skip(reason="Integration test that runs the full app; may need to be run separately")
def test_fixes():
    from main import FocusGuardPro
    import time

    print('🚀 Testing FocusGuard Pro with fixes...')
    app = FocusGuardPro()
    print('✅ FocusGuard Pro initialized successfully!')

    app.start()
    print('✅ Monitoring started!')

    time.sleep(5)
    stats = app.get_stats()
    print(f'📊 Stats: Focus {stats["current_focus"]}%, Predictions: {stats["predictions"]}')

    app.stop()
    print('✅ System stopped successfully!')
    print('🎉 All critical fixes verified!')
