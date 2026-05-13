#!/usr/bin/env python3
"""动态权重公式 α = f(Δ) 可视化"""
import numpy as np
import matplotlib.pyplot as plt

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def compute_alpha(delta, base=0.5, scale=2.0, lambda_=1.0):
    sig = sigmoid(lambda_ * delta)
    alpha = base + (sig - 0.5) * scale
    return np.clip(alpha, 0.1, 0.9)

# 数据
delta = np.linspace(-1, 1, 500)
alpha = compute_alpha(delta)

# 绘图
plt.figure(figsize=(10, 6))
plt.plot(delta, alpha, 'purple', linewidth=3, label='α')
plt.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='α = 0.5')
plt.fill_between(delta, alpha, 0.5, where=(alpha > 0.5), alpha=0.2, color='green', label='Trust NLI')
plt.fill_between(delta, alpha, 0.5, where=(alpha < 0.5), alpha=0.2, color='blue', label='Trust Embedding')

plt.xlabel('Δ (gap_nli - gap_emb)', fontsize=12)
plt.ylabel('α', fontsize=12)
plt.title('Dynamic Weight: α = clamp(0.5 + 2.0 × (σ(Δ) - 0.5), 0.1, 0.9)', fontsize=13)
plt.xlim(-1, 1)
plt.ylim(0, 1)
plt.legend(loc='upper left')
plt.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig('/root/autodl-tmp/BY/DNNC-few-shot-intent-master/canvas/dynamic_alpha.png', dpi=150, facecolor='white')
print('Saved: dynamic_alpha.png')
plt.show()
