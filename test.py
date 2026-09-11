import matplotlib.pyplot as plt
import numpy as np
import requests


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:155.0) Gecko/20100101 Firefox/155.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    # 'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Referer': 'https://formula-timer.com/',
    'Origin': 'https://formula-timer.com',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'Priority': 'u=4',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    # Requests doesn't support trailers
    # 'TE': 'trailers',
}

res = requests.get('https://api.multiviewer.app/api/v1/circuits/39/2026', headers=headers)
print(res.text)
data = res.json()

x = np.array(data['x'])
y = np.array(data['y'])

# Optional: apply the track rotation
theta = np.radians(data['rotation'])
c, s = np.cos(theta), np.sin(theta)
R = np.array(((c, -s), (s, c)))
rotated = R.dot(np.vstack((x, y)))
rx, ry = rotated[0], rotated[1]

# Plot track layout
plt.figure(figsize=(10, 8))
# Faint track outline underneath so gaps between lego bricks are clear
plt.plot(rx, ry, color='#d3d3d3', linewidth=2, linestyle='--', zorder=1, label=f"{data['circuitName']} Track Line")

# Annotate corners
for corner in data['corners']:
    cx, cy = corner['trackPosition']['x'], corner['trackPosition']['y']
    rc = R.dot(np.array([cx, cy]))
    plt.scatter(rc[0], rc[1], color='red', s=35, zorder=5)
    plt.text(
        rc[0] + 60,
        rc[1] + 60,
        f"T{corner['number']}",
        fontsize=8,
        color='darkred',
        fontweight='bold',
        zorder=6
    )

mini_secs = data['miniSectorsIndexes']
mini_sec_pairs = list(zip(mini_secs, mini_secs[1:] + mini_secs[:1]))

# -------------------------------------------------------------
# Fetch Telemetry Data (Andrea Kimi Antonelli - Lap 7 - Monza)
# -------------------------------------------------------------
tel_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:155.0) Gecko/20100101 Firefox/155.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://tracinginsights.com/',
    'Origin': 'https://tracinginsights.com',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'Priority': 'u=4',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}

tel_response = requests.get(
    'https://cdn.jsdelivr.net/gh/TracingInsights/2026@main/Italian%20Grand%20Prix/Race/ANT/7_tel.json',
    headers=tel_headers,
)
tel_data = tel_response.json().get('tel', {})

# Extract coordinates and timestamps
tel_x = np.array(tel_data['x'])
tel_y = np.array(tel_data.get('y', []))
tel_time = np.array(tel_data.get('time', []))

# -------------------------------------------------------------
# Match Telemetry with Mini-Sectors & Calculate Sector Times
# -------------------------------------------------------------
tel_pts = np.column_stack((tel_x, tel_y))

tspeed_ms = np.array(tel_data.get('speed', [])) / 3.6  # Convert km/h to m/s

boundary_times = []
boundary_distances = []
time_corrections = []
lateral_errors = []
corrected_boundary_positions = []

for ms_idx in mini_secs:
    pt = np.array([x[ms_idx], y[ms_idx]])
    dists = np.linalg.norm(tel_pts - pt, axis=1)
    k = np.argmin(dists)

    # Determine whether the boundary lies on segment (k-1, k) or (k, k+1)
    best_seg = (k - 1, k) if k > 0 else (k, k + 1)
    best_alpha = 0.0
    best_perp = dists[k]

    # Test candidate segments
    for i1, i2 in [(k - 1, k), (k, k + 1)]:
        if 0 <= i1 and i2 < len(tel_pts):
            u = tel_pts[i2] - tel_pts[i1]
            L2 = np.dot(u, u)
            if L2 > 0:
                alpha = np.dot(pt - tel_pts[i1], u) / L2
                perp = np.linalg.norm(pt - (tel_pts[i1] + alpha * u))
                if -0.2 <= alpha <= 1.2 and perp <= best_perp:
                    best_seg = (i1, i2)
                    best_alpha = alpha
                    best_perp = perp

    # High-accuracy interpolated crossing time and position
    idx1, idx2 = best_seg
    t_interp = tel_time[idx1] + best_alpha * (tel_time[idx2] - tel_time[idx1])
    pos_interp = tel_pts[idx1] + best_alpha * (tel_pts[idx2] - tel_pts[idx1])
    dt = t_interp - tel_time[k]   # Signed adjustment (adds or reduces time)
    d_along = dt * tspeed_ms[k]    # Distance along-track

    boundary_times.append(t_interp)
    boundary_distances.append(abs(d_along))
    time_corrections.append(dt)
    lateral_errors.append(best_perp)
    corrected_boundary_positions.append(pos_interp)

print(f"\nAverage raw distance error: {np.mean([np.min(np.linalg.norm(tel_pts - [x[m], y[m]], axis=1)) for m in mini_secs]):.2f} m")
print(f"Average lateral accuracy (car to track line): {np.mean(lateral_errors):.2f} m")

# -------------------------------------------------------------
# Calculate Estimated Duration for Each Mini-Sector
# -------------------------------------------------------------
minisector_times = []
print("\n--- Estimated High-Accuracy Mini-Sector Times (ANT Lap 7) ---")
for i, (b_start, b_end) in enumerate(zip(boundary_times, boundary_times[1:] + boundary_times[:1]), 1):
    if i < len(boundary_times):
        dt = b_end - b_start
    else:
        # Wrap-around across start/finish line
        dt = (tel_time[-1] - b_start) + (b_end - tel_time[0])
    minisector_times.append(dt)
    print(f"Mini-Sector {i:02d}: {dt:.3f} s (boundary adj: {time_corrections[i - 1]:+.3f} s)")

print(f"Total Lap Time: {sum(minisector_times):.3f} s (Actual: {tel_time[-1]:.3f} s)\n")


# Vibrant palette to make each lego brick stand out
palette = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#42d4f4', '#f032e6']

for i, (start, end) in enumerate(mini_sec_pairs, 1):
    # Handle wrap-around across start/finish line (index 751 -> 33)
    if start < end:
        sec_x = rx[start:end]
        sec_y = ry[start:end]
    else:
        sec_x = np.concatenate([rx[start:], rx[:end]])
        sec_y = np.concatenate([ry[start:], ry[:end]])

    # Create a visible space (gap) between each brick by trimming endpoints
    gap = max(1, int(len(sec_x) * 0.12))
    brick_x = sec_x[gap:-gap] if len(sec_x) > 2 * gap else sec_x
    brick_y = sec_y[gap:-gap] if len(sec_y) > 2 * gap else sec_y

    color = palette[(i - 1) % len(palette)]

    # Draw individual "Lego brick"
    plt.plot(
        brick_x,
        brick_y,
        color=color,
        linewidth=6,
        solid_capstyle='round',
        zorder=1
    )

    # Position the mini-sector number and duration at the exact midpoint along the curve
    mid = len(brick_x) // 2
    ms_time_str = f"{i}\n{minisector_times[i - 1]:.2f}s"
    plt.text(
        brick_x[mid],
        brick_y[mid],
        ms_time_str,
        fontsize=6,
        color='white',
        fontweight='bold',
        ha='center',
        va='center',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.75, edgecolor='none'),
        zorder=7
    )

# Overlay telemetry car trajectory rotated to match the track
if len(tel_x) > 0 and len(tel_y) > 0:
    tel_rot = R.dot(np.vstack((tel_x, tel_y)))
    plt.plot(tel_rot[0], tel_rot[1], color='#00d2be', linewidth=2, linestyle='-', zorder=2, label='ANT Lap 7 Telemetry Line')

plt.title(f"{data['circuitName']} Circuit Layout ({data['year']}) - Lap Time: {tel_time[-1]:.3f}s")
plt.axis('equal')
plt.axis('off')
plt.legend()

# -------------------------------------------------------------
# Figure 2: Telemetry Matching Accuracy / Distances
# -------------------------------------------------------------
fig2, ax2 = plt.subplots(figsize=(12, 5))
ms_labels = [f"MS {i}" for i in range(1, len(boundary_distances) + 1)]
bars = ax2.bar(ms_labels, boundary_distances, color='#4363d8', edgecolor='black', alpha=0.85)

mean_dist = np.mean(boundary_distances)
ax2.axhline(mean_dist, color='red', linestyle='--', linewidth=1.5, label=f'Mean Distance: {mean_dist:.2f} m')

# Add distance value labels on top of each bar
for bar in bars:
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width() / 2, height + 1.5, f'{height:.1f}m', ha='center', va='bottom', fontsize=7)

ax2.set_xlabel('Mini-Sector Boundary')
ax2.set_ylabel('Distance Error to Nearest Telemetry Point (meters)')
ax2.set_title('Accuracy Check: Distance Between Track Boundary Points and Closest Telemetry Point')
ax2.set_xticks(range(len(ms_labels)))
ax2.set_xticklabels(ms_labels, rotation=45, ha='right')
ax2.set_ylim(0, max(boundary_distances) * 1.15)
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend()
plt.tight_layout()


fig3, ax3 = plt.subplots(figsize=(12, 8))

# 1. Plot the telemetry dots in the background (green)
if len(tel_x) > 0 and len(tel_y) > 0:
    tel_rot = R.dot(np.vstack((tel_x, tel_y)))
    ax3.scatter(tel_rot[0], tel_rot[1], color='green', s=8, alpha=0.5, label='Telemetry Dots', zorder=20)


# 3. Highlight the original track cut-points in red
for i, ms_idx in enumerate(mini_secs):
    ax3.scatter(rx[ms_idx], ry[ms_idx], color='red', s=50, edgecolors='black', zorder=4, label='Original Track Cut-Points' if i == 0 else None)

# 4. Highlight the corrected boundary positions in blue (on car trajectory)
if len(corrected_boundary_positions) > 0:
    corr_rot = R.dot(np.array(corrected_boundary_positions).T)
    ax3.scatter(corr_rot[0], corr_rot[1], color='blue', s=55, edgecolors='white', linewidths=1.2, zorder=6, label='Corrected Boundaries')

ax3.set_title("Track Mini-Sectors vs Telemetry Points (Red: Original, Blue: Corrected)")
ax3.axis('equal')
ax3.axis('off')
ax3.legend()

plt.show()
