import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# ---- Load data ----

results = []
with open('results.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        row['match'] = int(row['match'])
        row['n_games'] = int(row['n_games'])
        row['p1_wins'] = int(row['p1_wins'])
        row['p2_wins'] = int(row['p2_wins'])
        row['draws'] = int(row['draws'])
        row['p1_winrate'] = float(row['p1_winrate'])
        results.append(row)

timing = {}
with open('timing.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        timing[row['algorithm']] = float(row['avg_time_per_move'])

# Style defaults
plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'font.size': 11,
})

COLORS = {
    'FlatMC': '#95a5a6',
    'UCT': '#3498db',
    'RAVE': '#2ecc71',
    'GRAVE': '#27ae60',
    'PPAF': '#e74c3c',
    'PPAFM': '#c0392b',
    'GRAVEPolicyBias': '#8e44ad',
}


# ===================================================================
# Plot 1: Win rate of each algorithm vs UCT baseline
# ===================================================================

def plot_vs_uct():
    # Extract matches where player2 is UCT (matches 2, 4, 5, 7)
    vs_uct = {}
    for r in results:
        if r['player2'] == 'UCT':
            vs_uct[r['player1']] = r['p1_winrate']
        elif r['player1'] == 'UCT':
            vs_uct[r['player2']] = 1.0 - r['p1_winrate']

    algos = ['RAVE', 'GRAVE', 'PPAF', 'PPAFM', 'GRAVEPolicyBias']
    # For GRAVEPolicyBias vs UCT, we don't have a direct match.
    # Compute from chain: skip if missing
    algos_present = [a for a in algos if a in vs_uct]
    rates = [vs_uct[a] * 100 for a in algos_present]
    colors = [COLORS.get(a, '#666') for a in algos_present]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(algos_present, rates, color=colors, width=0.6, edgecolor='white', linewidth=1.5)
    ax.axhline(y=50, color='#bbb', linestyle='--', linewidth=1, zorder=0)
    ax.set_ylabel('Win Rate vs UCT (%)')
    ax.set_title('Algorithm Performance vs UCT Baseline (1000 playouts, 100 games)')
    ax.set_ylim(0, 100)
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                f'{rate:.0f}%', ha='center', va='bottom', fontweight='bold', fontsize=10)
    plt.tight_layout()
    plt.savefig('plot_vs_uct.png', dpi=150)
    plt.close()
    print('Saved plot_vs_uct.png')


# ===================================================================
# Plot 2: Progression chart UCT -> RAVE -> GRAVE -> PPAF -> GPB
# ===================================================================

def plot_progression():
    # Show win rates along the improvement chain
    # UCT baseline = 50% (against itself), then each vs previous
    chain = [
        ('UCT', 50.0),          # baseline
    ]
    # Match 2: RAVE vs UCT
    for r in results:
        if r['match'] == 2:
            chain.append(('RAVE', r['p1_winrate'] * 100))
        elif r['match'] == 3:
            chain.append(('GRAVE', r['p1_winrate'] * 100))
    # PPAF vs UCT (match 5) — show vs UCT for consistency
    for r in results:
        if r['match'] == 5:
            chain.append(('PPAF', r['p1_winrate'] * 100))
        elif r['match'] == 8:
            chain.append(('GRAVE+PPAF', r['p1_winrate'] * 100))

    labels = [c[0] for c in chain]
    values = [c[1] for c in chain]
    colors = [COLORS.get(l, '#8e44ad') for l in labels]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(range(len(labels)), values, 'o-', color='#2c3e50', linewidth=2, markersize=8, zorder=3)
    for i, (label, val) in enumerate(chain):
        ax.bar(i, val, color=colors[i], alpha=0.4, width=0.5, zorder=1)
        ax.text(i, val + 1.5, f'{val:.0f}%', ha='center', fontweight='bold', fontsize=10)
    ax.axhline(y=50, color='#bbb', linestyle='--', linewidth=1, zorder=0)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_ylabel('Win Rate vs Previous Algorithm (%)')
    ax.set_title('Algorithm Progression (each vs predecessor, 1000 playouts)')
    ax.set_ylim(0, 100)
    plt.tight_layout()
    plt.savefig('plot_progression.png', dpi=150)
    plt.close()
    print('Saved plot_progression.png')


# ===================================================================
# Plot 3: Time per move bar chart
# ===================================================================

def plot_timing():
    order = ['FlatMC', 'UCT', 'RAVE', 'GRAVE', 'PPAF', 'PPAFM', 'GRAVEPolicyBias']
    algos = [a for a in order if a in timing]
    times = [timing[a] for a in algos]
    colors = [COLORS.get(a, '#666') for a in algos]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(algos, times, color=colors, width=0.6, edgecolor='white', linewidth=1.5)
    ax.set_ylabel('Average Time per Move (seconds)')
    ax.set_title('Algorithm Speed Comparison (1000 playouts)')
    for bar, t in zip(bars, times):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f'{t:.2f}s', ha='center', va='bottom', fontsize=10)
    ax.set_ylim(0, max(times) * 1.2)
    plt.xticks(rotation=15, ha='right')
    plt.tight_layout()
    plt.savefig('plot_timing.png', dpi=150)
    plt.close()
    print('Saved plot_timing.png')


# ===================================================================
# Plot 4: Head-to-head matrix heatmap
# ===================================================================

def plot_heatmap():
    all_algos = ['FlatMC', 'UCT', 'RAVE', 'GRAVE', 'PPAF', 'PPAFM', 'GRAVEPolicyBias']
    n = len(all_algos)
    matrix = np.full((n, n), np.nan)

    for r in results:
        p1, p2 = r['player1'], r['player2']
        if p1 in all_algos and p2 in all_algos:
            i = all_algos.index(p1)
            j = all_algos.index(p2)
            matrix[i][j] = r['p1_winrate'] * 100
            matrix[j][i] = (1.0 - r['p1_winrate']) * 100

    fig, ax = plt.subplots(figsize=(8, 7))
    cmap = plt.cm.RdYlGn
    im = ax.imshow(matrix, cmap=cmap, vmin=20, vmax=80, aspect='auto')

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(all_algos, rotation=35, ha='right', fontsize=9)
    ax.set_yticklabels(all_algos, fontsize=9)

    # Annotate cells
    for i in range(n):
        for j in range(n):
            if not np.isnan(matrix[i][j]):
                val = matrix[i][j]
                color = 'white' if val < 35 or val > 65 else 'black'
                ax.text(j, i, f'{val:.0f}%', ha='center', va='center',
                        fontsize=10, fontweight='bold', color=color)
            elif i == j:
                ax.text(j, i, '-', ha='center', va='center',
                        fontsize=10, color='#999')

    ax.set_title('Head-to-Head Win Rates (row vs column)')
    ax.set_xlabel('Opponent')
    ax.set_ylabel('Algorithm')
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Win Rate (%)')
    plt.tight_layout()
    plt.savefig('plot_heatmap.png', dpi=150)
    plt.close()
    print('Saved plot_heatmap.png')


# ===================================================================

if __name__ == '__main__':
    plot_vs_uct()
    plot_progression()
    plot_timing()
    plot_heatmap()
    print('\nAll plots generated.')
