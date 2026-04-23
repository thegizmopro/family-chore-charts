/**
 * Chore balancer — distributes chores across groups by weekly time load.
 *
 * Algorithm: greedy bin-packing. Sort chores by descending weekly minutes,
 * then assign each chore to whichever group currently has the lowest total.
 * Ties broken by group index (A before B before C). Produces near-optimal
 * balance in O(n log n).
 */

const GROUP_LABELS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';

/**
 * Total minutes a chore takes per week.
 * as_needed chores use instances_per_week as-is (best estimate).
 */
function weeklyMinutes(chore) {
  return chore.minutes * chore.instances_per_week;
}

/**
 * Balance chores across numGroups groups.
 *
 * @param {Array}  chores     - chores array from chore_schema.json
 * @param {number} numGroups  - number of groups (2–26)
 * @returns {{ groups: Object, group_totals_minutes_per_week: Object }}
 */
function balanceChores(chores, numGroups) {
  if (!chores || chores.length === 0) throw new Error('chores array is empty');
  if (numGroups < 2 || numGroups > 26) throw new Error('numGroups must be 2–26');

  const labels = GROUP_LABELS.slice(0, numGroups).split('');

  // Sort a copy — heaviest chores first
  const sorted = [...chores].sort((a, b) => weeklyMinutes(b) - weeklyMinutes(a));

  // Initialise group state
  const groups  = {};
  const totals  = {};
  for (const label of labels) {
    groups[label] = [];
    totals[label] = 0;
  }

  // Greedy assignment
  for (const chore of sorted) {
    // Find the label with the lowest current total (ties → first label wins)
    let minLabel = labels[0];
    for (const label of labels) {
      if (totals[label] < totals[minLabel]) minLabel = label;
    }
    groups[minLabel].push(chore.id);
    totals[minLabel] += weeklyMinutes(chore);
  }

  return {
    groups,
    group_totals_minutes_per_week: totals,
  };
}

/**
 * Convenience: run balancer against a full schema object and return the
 * updated schema with groups and totals filled in.
 */
function applyBalancer(schema) {
  const { groups, group_totals_minutes_per_week } = balanceChores(
    schema.chores,
    schema.num_groups
  );
  return { ...schema, groups, group_totals_minutes_per_week };
}

// --- Node / browser dual export ---
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { weeklyMinutes, balanceChores, applyBalancer };
}
