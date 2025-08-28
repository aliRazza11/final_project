import numpy as np
import pytest

from app.domain.BetaScheduler import BetaScheduler
from app.domain.Diffusion import Diffusion

@pytest.fixture
def sample_diffusion():
    steps = 10
    sched = BetaScheduler(steps)
    x0 = np.ones((8, 8, 3), dtype=np.float32) * 0.5
    return Diffusion(
        x0,
        sched.beta,
        sched.alpha,
        sched.alpha_bar,
        sched.get_all().sqrt_alpha_bar,
        sched.get_all().sqrt_one_minus_alpha_bar,
        sched.get_all().sqrt_one_minus_beta,
        seed=42,
    )

def test_noise_variance(sample_diffusion):
    t = 3
    xt = sample_diffusion.closed_form_diffusion(t)
    expected_var = 1.0 - sample_diffusion.alpha_bar[t]
    actual_var = np.var(xt - sample_diffusion.sqrt_alpha_bar[t]*sample_diffusion.x0)
    np.testing.assert_allclose(actual_var, expected_var, rtol=0.1)

def test_output_shape(sample_diffusion):
    t = sample_diffusion.steps // 2
    xt = sample_diffusion.closed_form_diffusion(t)
    assert xt.shape == sample_diffusion.img_shape

def test_output_type(sample_diffusion):
    xt = sample_diffusion.closed_form_diffusion(0)
    assert isinstance(xt, np.ndarray)
    assert xt.dtype == np.float32

def test_variance_increases(sample_diffusion):
    var0 = np.var(sample_diffusion.closed_form_diffusion(0))
    varT = np.var(sample_diffusion.closed_form_diffusion(sample_diffusion.steps-1))
    assert varT > var0

def test_mean_preservation_closed(sample_diffusion):
    x0_mean = np.mean(sample_diffusion.x0)
    xt_mean = np.mean(sample_diffusion.closed_form_diffusion(sample_diffusion.steps-1))
    # Should still be in reasonable range
    assert abs(xt_mean - x0_mean) < 0.1

def test_mean_preservation_iterative(sample_diffusion):
    x0_mean = np.mean(sample_diffusion.x0)
    xt_mean = np.mean(sample_diffusion.iterative_diffusion(sample_diffusion.steps-1))
    # Should still be in reasonable range
    assert abs(xt_mean - x0_mean) < 0.1

def test_reproducibility_closed(sample_diffusion):
    xt1 = sample_diffusion.closed_form_diffusion(5)
    xt2 = sample_diffusion.closed_form_diffusion(5)
    np.testing.assert_allclose(xt1, xt2)

def test_reproducibility_iterative(sample_diffusion):
    xt1 = sample_diffusion.iterative_diffusion(5)
    xt2 = sample_diffusion.iterative_diffusion(5)
    np.testing.assert_allclose(xt1, xt2)

def test_different_seeds(sample_diffusion):
    sample_diffusion._base_seed += 1
    xt_new = sample_diffusion.closed_form_diffusion(5)
    sample_diffusion._base_seed -= 1
    xt_old = sample_diffusion.closed_form_diffusion(5)
    assert not np.allclose(xt_new, xt_old)

# def test_invalid_timestep(sample_diffusion):
#     with pytest.raises(TypeError):
#         sample_diffusion.closed_form_diffusion("a")
#     with pytest.raises(TypeError):
#         sample_diffusion.closed_form_diffusion(-1)
#     with pytest.raises(ValueError):
#         sample_diffusion.closed_form_diffusion(sample_diffusion.steps)

def test_last_step_shape(sample_diffusion):
    xt = sample_diffusion.iterative_diffusion(sample_diffusion.steps-1)
    assert xt.shape == sample_diffusion.img_shape