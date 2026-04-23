const { weeklyMinutes, balanceChores, applyBalancer } = require('./balancer');
const schema = require('./chore_schema.json');

// --- helpers ---
function totalForGroup(chores, ids) {
  return ids.reduce((sum, id) => {
    const c = chores.find(ch => ch.id === id);
    return sum + (c ? weeklyMinutes(c) : 0);
  }, 0);
}

function maxVariancePct(totals) {
  const vals = Object.values(totals);
  const max = Math.max(...vals);
  const min = Math.min(...vals);
  return max === 0 ? 0 : ((max - min) / max) * 100;
}

// --- tests ---
let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  ✓ ${name}`);
    passed++;
  } catch (e) {
    console.error(`  ✗ ${name}`);
    console.error(`    ${e.message}`);
    failed++;
  }
}

function assert(condition, message) {
  if (!condition) throw new Error(message || 'assertion failed');
}

function assertEqual(a, b, message) {
  if (a !== b) throw new Error(message || `expected ${b}, got ${a}`);
}

console.log('\nbalancer.js tests\n');

// weeklyMinutes
console.log('weeklyMinutes()');
test('fixed-schedule chore: minutes × instances', () => {
  assertEqual(weeklyMinutes({ minutes: 10, instances_per_week: 3 }), 30);
});
test('as_needed chore uses instances_per_week as estimate', () => {
  assertEqual(weeklyMinutes({ minutes: 3, instances_per_week: 2, as_needed: true }), 6);
});
test('once-a-week chore', () => {
  assertEqual(weeklyMinutes({ minutes: 15, instances_per_week: 1 }), 15);
});

// balanceChores — seed schema
console.log('\nbalanceChores() — seed schema');
const result = balanceChores(schema.chores, schema.num_groups);

test('returns groups object with correct number of keys', () => {
  assertEqual(Object.keys(result.groups).length, schema.num_groups);
});
test('every chore assigned to exactly one group', () => {
  const allAssigned = Object.values(result.groups).flat().sort((a, b) => a - b);
  const allIds = schema.chores.map(c => c.id).sort((a, b) => a - b);
  assert(
    JSON.stringify(allAssigned) === JSON.stringify(allIds),
    `assigned ${JSON.stringify(allAssigned)} — expected ${JSON.stringify(allIds)}`
  );
});
test('no chore appears in more than one group', () => {
  const all = Object.values(result.groups).flat();
  const unique = new Set(all);
  assertEqual(unique.size, all.length, 'duplicate chore assignment detected');
});
test('totals match actual chore minutes', () => {
  for (const [label, ids] of Object.entries(result.groups)) {
    const actual = totalForGroup(schema.chores, ids);
    assertEqual(
      result.group_totals_minutes_per_week[label],
      actual,
      `group ${label}: reported ${result.group_totals_minutes_per_week[label]}, actual ${actual}`
    );
  }
});
test('variance across groups is ≤ 15%', () => {
  const variance = maxVariancePct(result.group_totals_minutes_per_week);
  assert(variance <= 15, `variance ${variance.toFixed(1)}% exceeds 15%`);
});
test('seed schema balances to ≤ 5% variance (greedy should nail this)', () => {
  const variance = maxVariancePct(result.group_totals_minutes_per_week);
  assert(variance <= 5, `variance ${variance.toFixed(1)}% — expected ≤ 5% for seed data`);
});

// edge cases
console.log('\nbalanceChores() — edge cases');
test('2 groups', () => {
  const r = balanceChores(schema.chores, 2);
  assertEqual(Object.keys(r.groups).length, 2);
  assert('A' in r.groups && 'B' in r.groups);
});
test('5 groups', () => {
  const r = balanceChores(schema.chores, 5);
  assertEqual(Object.keys(r.groups).length, 5);
});
test('single chore goes to group A', () => {
  const r = balanceChores([{ id: 1, minutes: 10, instances_per_week: 2 }], 3);
  assert(r.groups.A.includes(1));
  assertEqual(r.groups.B.length, 0);
  assertEqual(r.groups.C.length, 0);
});
test('equal-weight chores distribute round-robin by label', () => {
  const chores = [1, 2, 3, 4, 5, 6].map(id => ({
    id,
    minutes: 5,
    instances_per_week: 1,
  }));
  const r = balanceChores(chores, 3);
  assertEqual(r.groups.A.length, 2);
  assertEqual(r.groups.B.length, 2);
  assertEqual(r.groups.C.length, 2);
});
test('throws on empty chores array', () => {
  let threw = false;
  try { balanceChores([], 3); } catch { threw = true; }
  assert(threw, 'expected error for empty chores');
});
test('throws on numGroups < 2', () => {
  let threw = false;
  try { balanceChores(schema.chores, 1); } catch { threw = true; }
  assert(threw, 'expected error for numGroups=1');
});
test('throws on numGroups > 26', () => {
  let threw = false;
  try { balanceChores(schema.chores, 27); } catch { threw = true; }
  assert(threw, 'expected error for numGroups=27');
});

// applyBalancer
console.log('\napplyBalancer()');
test('returns schema with groups and totals filled in', () => {
  const updated = applyBalancer(schema);
  assert(updated.groups !== null);
  assert(Object.keys(updated.group_totals_minutes_per_week).length === schema.num_groups);
});
test('does not mutate the input schema', () => {
  const before = JSON.stringify(schema.groups);
  applyBalancer(schema);
  assertEqual(JSON.stringify(schema.groups), before);
});

// summary
console.log(`\n${passed} passed, ${failed} failed\n`);
if (failed > 0) process.exit(1);
