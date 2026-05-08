var GIT_STATUS_DISPLAY = {
  'clean':     '✓ clean',
  'dirty':     '⚠ dirty',
  'unmanaged': '— git未管理',
  'detached':  'detached',
  'unknown':   '? unknown'
};

var OPERATIONAL_STATUS_DISPLAY = {
  'READY':          '● READY',
  'BLOCKED':        '✖ BLOCKED',
  'WAITING_HUMAN':  '⏳ WAITING_HUMAN',
  'RUNNING':        '▶ RUNNING',
  'DONE':           '✓ DONE',
  'UNKNOWN':        '? UNKNOWN'
};

var FIELDS = [
  'project_id', 'repo_path', 'branch', 'HEAD',
  'git_status', 'latest_session', 'four_gate',
  'failure_type', 'human_gate', 'artifacts'
];

function renderCards(projects) {
  var cards = document.querySelectorAll('.project-card');
  projects.forEach(function(proj, i) {
    var card = cards[i];
    if (!card) return;

    FIELDS.forEach(function(field) {
      var el = card.querySelector('[data-field="' + field + '"]');
      if (!el) return;

      if (field === 'git_status') {
        var status = proj[field] || 'unknown';
        var text = GIT_STATUS_DISPLAY[status] || status;
        el.textContent = text;
        el.className = 'value badge badge-' + status;
      } else {
        var val = proj[field];
        el.textContent = (val == null || val === '' || val === '—') ? '—' : val;
      }
    });

    var V5_FIELDS = ['operational_status', 'next_action', 'blocker_summary'];
    V5_FIELDS.forEach(function(field) {
      var el = card.querySelector('[data-v5-field="' + field + '"]');
      if (!el) return;

      if (field === 'operational_status') {
        var opStatus = proj[field] || 'UNKNOWN';
        var opText = OPERATIONAL_STATUS_DISPLAY[opStatus] || opStatus;
        el.textContent = opText;
        el.className = 'value badge badge-op-' + opStatus.toLowerCase().replace(/_/g, '-');
      } else {
        var val = proj[field];
        el.textContent = (val == null || val === '') ? '—' : val;
      }
    });

    var queueEl = card.querySelector('.queue-summary');
    if (queueEl) {
      var qs = proj['queue_summary'];
      if (qs === 'not_configured' || qs == null) {
        queueEl.textContent = '—（未設定）';
        queueEl.className = 'queue-summary badge badge-not-configured';
      } else {
        queueEl.textContent = qs;
        queueEl.className = 'queue-summary badge';
      }
    }
  });
}

function loadState() {
  fetch('/api/state')
    .then(function(res) { return res.json(); })
    .then(function(data) { renderCards(data); })
    .catch(function(err) { console.error('PCC fetch error:', err); });
}

document.addEventListener('DOMContentLoaded', function() {
  loadState();
  document.getElementById('manual-refresh').addEventListener('click', function() {
    location.reload();
  });
});
