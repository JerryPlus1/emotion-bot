#!/usr/bin/env python3
"""
Dynamic Weight α Formula Visualization
动态权重公式可视化

Formula: α = clamp(base + scale * (sigmoid(λ * Δ) - 0.5), 0.1, 0.9)
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = False


def sigmoid(x):
    """Sigmoid function"""
    return 1 / (1 + np.exp(-x))


def compute_alpha(delta, base=0.5, scale=2.0, lambda_=1.0):
    """
    Compute dynamic alpha

    Args:
        delta: gap_nli - gap_emb
        base: base weight (default 0.5)
        scale: adjustment range (default 2.0)
        lambda_: sensitivity (default 1.0)

    Returns:
        alpha: clamped to [0.1, 0.9]
    """
    sig = sigmoid(lambda_ * delta)
    alpha = base + (sig - 0.5) * scale
    return np.clip(alpha, 0.1, 0.9)


# Create figure
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Dynamic Weight α = f(Δ)', fontsize=16, fontweight='bold', y=0.98)

# Color scheme
COLOR_ALPHA = '#a78bfa'
COLOR_SIGMOID = '#38bdf8'
COLOR_BASELINE = '#fb7185'
COLOR_NLI = '#4ade80'

# Delta range
delta = np.linspace(-1, 1, 500)

# ========== Plot 1: Basic Alpha Curve ==========
ax1 = axes[0, 0]
alpha = compute_alpha(delta, base=0.5, scale=2.0)
ax1.plot(delta, alpha, color=COLOR_ALPHA, linewidth=2.5, label='α')
ax1.axhline(y=0.5, color=COLOR_BASELINE, linestyle='--', alpha=0.7, label='α = 0.5 (baseline)')
ax1.axhline(y=0.9, color='gray', linestyle=':', alpha=0.4)
ax1.axhline(y=0.1, color='gray', linestyle=':', alpha=0.4)
ax1.fill_between(delta, alpha, 0.5, where=(alpha > 0.5), alpha=0.2, color=COLOR_NLI, label='Trust NLI')
ax1.fill_between(delta, alpha, 0.5, where=(alpha < 0.5), alpha=0.2, color=COLOR_SIGMOID, label='Trust Embedding')
ax1.set_xlabel('Δ (gap_nli - gap_emb)', fontsize=11)
ax1.set_ylabel('α', fontsize=11)
ax1.set_title('Default: base=0.5, scale=2.0, λ=1.0', fontsize=12)
ax1.set_xlim(-1, 1)
ax1.set_ylim(0, 1)
ax1.legend(loc='upper left', fontsize=9)
ax1.grid(True, alpha=0.2)

# ========== Plot 2: Effect of scale ==========
ax2 = axes[0, 1]
scales = [0.5, 1.0, 2.0, 3.0, 4.0]
colors_scale = plt.cm.viridis(np.linspace(0.2, 0.9, len(scales)))

for s, c in zip(scales, colors_scale):
    alpha = compute_alpha(delta, base=0.5, scale=s)
    ax2.plot(delta, alpha, linewidth=2, color=c, label=f'scale={s}')

ax2.axhline(y=0.5, color=COLOR_BASELINE, linestyle='--', alpha=0.7)
ax2.set_xlabel('Δ (gap_nli - gap_emb)', fontsize=11)
ax2.set_ylabel('α', fontsize=11)
ax2.set_title('Effect of scale (adjustment range)', fontsize=12)
ax2.set_xlim(-1, 1)
ax2.set_ylim(0, 1)
ax2.legend(loc='upper left', fontsize=9)
ax2.grid(True, alpha=0.2)

# ========== Plot 3: Effect of base ==========
ax3 = axes[1, 0]
bases = [0.3, 0.4, 0.5, 0.6, 0.7]
colors_base = plt.cm.coolwarm(np.linspace(0.2, 0.8, len(bases)))

for b, c in zip(bases, colors_base):
    alpha = compute_alpha(delta, base=b, scale=2.0)
    ax3.plot(delta, alpha, linewidth=2, color=c, label=f'base={b}')

ax3.axhline(y=0.5, color=COLOR_BASELINE, linestyle='--', alpha=0.7)
ax3.set_xlabel('Δ (gap_nli - gap_emb)', fontsize=11)
ax3.set_ylabel('α', fontsize=11)
ax3.set_title('Effect of base (center weight)', fontsize=12)
ax3.set_xlim(-1, 1)
ax3.set_ylim(0, 1)
ax3.legend(loc='upper left', fontsize=9)
ax3.grid(True, alpha=0.2)

# ========== Plot 4: Effect of lambda ==========
ax4 = axes[1, 1]
lambdas = [0.5, 1.0, 2.0, 3.0, 5.0]
colors_lambda = plt.cm.plasma(np.linspace(0.2, 0.9, len(lambdas)))

for l, c in zip(lambdas, colors_lambda):
    alpha = compute_alpha(delta, base=0.5, scale=2.0, lambda_=l)
    ax4.plot(delta, alpha, linewidth=2, color=c, label=f'λ={l}')

ax4.axhline(y=0.5, color=COLOR_BASELINE, linestyle='--', alpha=0.7)
ax4.set_xlabel('Δ (gap_nli - gap_emb)', fontsize=11)
ax4.set_ylabel('α', fontsize=11)
ax4.set_title('Effect of λ (sensitivity)', fontsize=12)
ax4.set_xlim(-1, 1)
ax4.set_ylim(0, 1)
ax4.legend(loc='upper left', fontsize=9)
ax4.grid(True, alpha=0.2)

plt.tight_layout(rect=[0, 0.03, 1, 0.95])

# Save figure
output_path = '/root/autodl-tmp/BY/DNNC-few-shot-intent-master/canvas/dynamic_alpha_formula.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
print(f'Figure saved to: {output_path}')

# ========== Additional: Sigmoid Function ==========
fig2, ax = plt.subplots(figsize=(10, 6))

# Sigmoid curve
sig_values = sigmoid(delta)
ax.plot(delta, sig_values, color=COLOR_SIGMOID, linewidth=3, label='σ(x) = 1/(1+e⁻ˣ)')

# Mark key points
ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5)
ax.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
ax.scatter([0], [0.5], color=COLOR_BASELINE, s=100, zorder=5, label='(0, 0.5)')
ax.scatter([-1, 1], [sigmoid(-1), sigmoid(1)], color='gray', s=80, zorder=5, alpha=0.6)

# Annotations
ax.annotate('(0, 0.5)\nInflection Point', xy=(0, 0.5), xytext=(0.3, 0.3),
            fontsize=10, arrowprops=dict(arrowstyle='->', color='gray'))
ax.annotate('σ(-1) ≈ 0.27', xy=(-1, sigmoid(-1)), xytext=(-0.9, 0.15),
            fontsize=10, color='#666')
ax.annotate('σ(1) ≈ 0.73', xy=(1, sigmoid(1)), xytext=(0.7, 0.85),
            fontsize=10, color='#666')

ax.set_xlabel('x', fontsize=12)
ax.set_ylabel('σ(x)', fontsize=12)
ax.set_title('Sigmoid Function', fontsize=14, fontweight='bold')
ax.set_xlim(-1, 1)
ax.set_ylim(0, 1)
ax.legend(loc='upper left', fontsize=11)
ax.grid(True, alpha=0.2)

output_path2 = '/root/autodl-tmp/BY/DNNC-few-shot-intent-master/canvas/sigmoid_function.png'
plt.savefig(output_path2, dpi=150, bbox_inches='tight', facecolor='white')
print(f'Figure saved to: {output_path2}')

# ========== Print Formula Summary ==========
print("\n" + "=" * 60)
print("DYNAMIC WEIGHT FORMULA SUMMARY")
print("=" * 60)
print("""
Formula:
    α = clamp(base + scale × (σ(λ × Δ) - 0.5), 0.1, 0.9)

Where:
    Δ  = gap_nli - gap_emb  (confidence difference)
    σ  = sigmoid function   = 1 / (1 + exp(-x))
    base   = base weight    (default: 0.5)
    scale  = adjustment range (default: 2.0)
    λ      = sensitivity     (default: 1.0)

Interpretation:
    Δ > 0 → NLI has higher confidence → α ↑ (trust NLI more)
    Δ < 0 → Embedding has higher confidence → α ↓ (trust Embedding more)
    Δ = 0 → Balanced fusion (α = base)

Examples:
    base=0.5, scale=2.0, λ=1.0:
        Δ = 0.5  → α ≈ 0.62  (slightly favor NLI)
        Δ = 1.0  → α ≈ 0.73  (favor NLI)
        Δ = -0.5 → α ≈ 0.38  (slightly favor Embedding)
        Δ = -1.0 → α ≈ 0.27  (favor Embedding)
""")
print("=" * 60)

plt.show()
