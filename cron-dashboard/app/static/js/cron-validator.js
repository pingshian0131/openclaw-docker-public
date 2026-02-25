document.addEventListener('DOMContentLoaded', function () {
  const input = document.getElementById('cronExpr');
  const preview = document.getElementById('cronPreview');
  if (!input || !preview) return;

  let timer = null;

  input.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(validate, 400);
  });

  // Validate on load if there's a value
  if (input.value.trim()) validate();

  function validate() {
    const expr = input.value.trim();
    if (!expr) {
      preview.innerHTML = '';
      return;
    }
    fetch('/api/cron/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ expression: expr }),
    })
      .then(r => r.json())
      .then(data => {
        if (data.valid) {
          preview.innerHTML =
            '<span class="text-success"><i class="bi bi-check-circle"></i> ' +
            data.description + '</span><br>' +
            '<small class="text-muted">Next: ' +
            data.next_runs.join(', ') + '</small>';
        } else {
          preview.innerHTML =
            '<span class="text-danger"><i class="bi bi-x-circle"></i> ' +
            (data.error || 'Invalid') + '</span>';
        }
      })
      .catch(() => {
        preview.innerHTML = '';
      });
  }
});
