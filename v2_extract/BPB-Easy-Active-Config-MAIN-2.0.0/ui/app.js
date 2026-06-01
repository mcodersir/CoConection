/* BPB Easy Active Config v2 — Frontend Logic — NO eval, NO new Function */
(function () {
  'use strict';

  var $ = function (q) { return document.querySelector(q); };
  var $$ = function (q) { return Array.from(document.querySelectorAll(q)); };

  function toast(msg) {
    var t = $('#toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(function () { t.classList.remove('show'); }, 3500);
  }

  async function post(path, body) {
    var res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {})
    });
    var data;
    try { data = await res.json(); } catch (e) {
      throw new Error('Server response could not be parsed.');
    }
    if (!data.ok) {
      var err = (data.deploy && data.deploy.errors && data.deploy.errors[0]) || {};
      throw new Error(data.error || err.help_fa || err.message || 'Unknown error');
    }
    return data;
  }

  function selected(selector) {
    return $$(selector + ':checked').map(function (x) { return x.value; });
  }

  function cfPayload() {
    return {
      api_token: $('#cfToken').value.trim(),
      account_id: $('#cfAccountId').value.trim(),
      worker_name: $('#workerName').value.trim() || 'bpb-panel',
      uuid: $('#bpbUuid').value.trim(),
      sub_path: $('#subPath').value.trim() || 'sub',
      proxy_ip: $('#proxyIp').value.trim()
    };
  }

  function scanPayload() {
    return {
      ip_text: $('#scannerIpText').value || '',
      random_count: parseInt($('#scanRandomCount').value || '0', 10),
      ip_limit: 900,
      timeout: parseInt($('#scanTimeout').value || '4', 10),
      workers: 64,
      ports: selected('.scan-port'),
      sni_host: 'speed.cloudflare.com'
    };
  }

  function runPayload() {
    return {
      subscription_url: $('#subUrl').value.trim(),
      timeout: parseInt($('#timeout').value || '7', 10),
      workers: parseInt($('#workers').value || '48', 10),
      limit: parseInt($('#limit').value || '2600', 10),
      random_count: parseInt($('#randomCount').value || '420', 10),
      mode: document.querySelector('input[name="mode"]:checked').value || 'auto',
      ip_list: $('#ipList').value || '',
      ports: selected('.port')
    };
  }

  // --- UUID Generation ---
  $('#genUuidBtn').addEventListener('click', function () {
    var u;
    if (crypto.randomUUID) {
      u = crypto.randomUUID();
    } else {
      u = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0;
        var v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      });
    }
    $('#bpbUuid').value = u;
    toast('UUID generated!');
  });

  // --- Cloudflare Verify ---
  $('#verifyCfBtn').addEventListener('click', async function () {
    var btn = this;
    btn.disabled = true;
    $('#cfResult').textContent = 'Verifying token...';
    try {
      var data = await post('/api/cf-verify', cfPayload());
      var accounts = data.accounts || [];
      $('#cfResult').textContent = 'Token valid!\nAccounts found:\n' +
        (accounts.map(function (a) { return '- ' + (a.name || 'Account') + ' | ' + a.id; }).join('\n') || 'No accounts; enter Account ID manually.');
      if (accounts.length && !$('#cfAccountId').value.trim()) {
        $('#cfAccountId').value = accounts[0].id;
      }
      toast('Token verified!');
    } catch (e) {
      $('#cfResult').textContent = 'Error: ' + e.message;
      toast('Token verification failed.');
    } finally { btn.disabled = false; }
  });

  // --- Cloudflare Deploy ---
  $('#deployCfBtn').addEventListener('click', async function () {
    var btn = this;
    btn.disabled = true;
    $('#cfResult').textContent = 'Deploying Worker to Cloudflare...';
    try {
      var data = await post('/api/cf-deploy', cfPayload());
      var lines = [data.ok ? 'Deploy successful!' : 'Deploy failed.'];
      if (data.worker_url_hint) {
        lines.push('');
        lines.push('Subscription URL:');
        lines.push(data.worker_url_hint);
        $('#subUrl').value = data.worker_url_hint;
      }
      if (data.next_steps_fa) {
        lines.push('');
        lines.push('Next steps:');
        data.next_steps_fa.forEach(function (x) { lines.push('- ' + x); });
      }
      $('#cfResult').textContent = lines.join('\n');
      toast('Deploy complete!');
    } catch (e) {
      $('#cfResult').textContent = 'Error: ' + e.message;
      toast('Deploy failed.');
    } finally { btn.disabled = false; }
  });

  // --- Paste ---
  $('#pasteBtn').addEventListener('click', async function () {
    try {
      $('#subUrl').value = await navigator.clipboard.readText();
      toast('Pasted from clipboard.');
    } catch (e) { toast('Clipboard paste failed; paste manually.'); }
  });

  // --- Check Link ---
  $('#fetchBtn').addEventListener('click', async function () {
    var btn = this;
    btn.disabled = true;
    try {
      var data = await post('/api/fetch', runPayload());
      var msg = 'Link OK!\nTotal lines: ' + data.total_lines + '\nSupported configs: ' + data.supported_configs;
      if (data.fetch_warning) msg = 'Warning: ' + data.fetch_warning + '\n\n' + msg;
      if (data.examples && data.examples.length) {
        msg += '\nSamples:\n- ' + data.examples.slice(0, 6).join('\n- ');
      }
      toast('Subscription fetched!');
      // Show in a simpler way
      $('#cfResult').textContent = msg;
    } catch (e) {
      toast('Fetch failed: ' + e.message);
    } finally { btn.disabled = false; }
  });

  // --- IP Scanner ---
  $('#scanIpBtn').addEventListener('click', async function () {
    var btn = this;
    btn.disabled = true;
    btn.textContent = 'Scanning...';
    $('#ipScanResult').textContent = 'Scanning started...';
    try {
      var data = await post('/api/scan-ips', scanPayload());
      var lines = ['Candidates: ' + data.candidate_count, 'Working endpoints: ' + data.working_count, ''];
      (data.top_results || []).slice(0, 20).forEach(function (r) {
        lines.push((r.ok ? 'OK' : 'FAIL') + ' | ' + r.endpoint + ' | ' + r.latency_ms + 'ms | ' + (r.message || ''));
      });
      lines.push('\nSaved to: ' + (data.files && data.files.clean || 'output/clean_ips.txt'));
      $('#ipScanResult').textContent = lines.join('\n');
      if (data.clean_ips && data.clean_ips.length) {
        window._lastCleanIps = data.clean_ips;
      }
      toast(data.working_count + ' clean endpoints found!');
    } catch (e) {
      $('#ipScanResult').textContent = 'Error: ' + e.message;
      toast('Scan failed.');
    } finally { btn.disabled = false; btn.textContent = 'Scan IPs'; }
  });

  $('#useCleanIpsBtn').addEventListener('click', function () {
    if (!window._lastCleanIps || !window._lastCleanIps.length) {
      toast('Run scanner first.');
      return;
    }
    $('#ipList').value = window._lastCleanIps.join('\n');
    var cleanRadio = document.querySelector('input[name="mode"][value="clean_ip"]');
    if (cleanRadio) cleanRadio.checked = true;
    toast('Clean IPs loaded!');
  });

  // --- Open Output ---
  $('#openOutputBtn').addEventListener('click', function () { fetch('/api/open-output'); });
  $('#openOutputBtn2').addEventListener('click', function () { fetch('/api/open-output'); });

  // --- RUN with SSE streaming ---
  $('#runBtn').addEventListener('click', function () {
    var btn = this;
    btn.disabled = true;
    btn.textContent = 'Running...';

    var progressDiv = $('#liveProgress');
    var progressFill = $('#progressFill');
    var progressText = $('#progressText');
    var resultsDiv = $('#results');
    var bestConfig = $('#bestConfig');

    progressDiv.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = 'Starting...';
    resultsDiv.innerHTML = '';
    bestConfig.value = '';

    var totalExpected = 0;
    var doneCount = 0;
    var workingCount = 0;
    var allResults = [];

    // Use fetch with ReadableStream for SSE
    var payload = runPayload();

    fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).then(function (response) {
      var reader = response.body.getReader();
      var decoder = new TextDecoder();
      var buffer = '';

      function processChunk() {
        return reader.read().then(function (result) {
          if (result.done) {
            btn.disabled = false;
            btn.textContent = 'Start — خروجی کانفیگ سالم';
            return;
          }

          buffer += decoder.decode(result.value, { stream: true });

          // Parse SSE events from buffer
          var parts = buffer.split('\n\n');
          buffer = parts.pop() || ''; // Keep incomplete event in buffer

          for (var i = 0; i < parts.length; i++) {
            var part = parts[i].trim();
            if (!part) continue;

            var eventType = '';
            var eventData = '';

            var lines = part.split('\n');
            for (var j = 0; j < lines.length; j++) {
              if (lines[j].startsWith('event: ')) {
                eventType = lines[j].substring(7).trim();
              } else if (lines[j].startsWith('data: ')) {
                eventData = lines[j].substring(6);
              }
            }

            if (!eventData) continue;

            var data;
            try { data = JSON.parse(eventData); } catch (e) { continue; }

            if (eventType === 'start') {
              progressText.textContent = data.message || 'Starting...';
            }
            else if (eventType === 'phase') {
              progressText.textContent = data.message || 'Processing...';
            }
            else if (eventType === 'progress') {
              doneCount = data.done;
              totalExpected = data.total || totalExpected;
              if (totalExpected > 0) {
                progressFill.style.width = Math.round((doneCount / totalExpected) * 100) + '%';
              }
              progressText.textContent = 'Testing ' + doneCount + '/' + totalExpected + ' — ' + (data.ok ? 'OK' : 'FAIL') + ' ' + data.endpoint;

              if (data.ok) workingCount++;

              // Add result to list (show latest first)
              allResults.push(data);
              renderResult(data, resultsDiv);
            }
            else if (eventType === 'done') {
              progressFill.style.width = '100%';
              progressText.textContent = 'تمام شد! ' + (data.working_count || 0) + ' working configs found.';

              if (data.best && data.best.config) {
                bestConfig.value = data.best.config;
              } else if (data.working_count === 0) {
                bestConfig.value = 'کانفیگ سالم پیدا نشد. Deploy را چک کن یا دوباره Start را بزن تا Nova endpointهای بیشتری تست کند.';
              }

              if (data.warnings && data.warnings.length) {
                toast('Done with warnings: ' + data.warnings[0]);
              } else {
                toast('تمام شد! ' + (data.working_count || 0) + ' کانفیگ سالم پیدا شد.');
              }

              // Also render any top_results from final payload
              if (data.top_results && data.top_results.length && allResults.length === 0) {
                data.top_results.forEach(function (r) { renderResult(r, resultsDiv); });
              }

              btn.disabled = false;
              btn.textContent = 'Start — خروجی کانفیگ سالم';
            }
          }

          return processChunk();
        });
      }

      return processChunk();
    }).catch(function (err) {
      progressText.textContent = 'Error: ' + err.message;
      btn.disabled = false;
      btn.textContent = 'Start — خروجی کانفیگ سالم';
      toast('Connection error. Retrying without streaming...');

      // Fallback to regular POST
      post('/api/run', payload).then(function (data) {
        if (data.best && data.best.config) {
          bestConfig.value = data.best.config;
        }
        if (data.top_results) {
          data.top_results.forEach(function (r) { renderResult(r, resultsDiv); });
        }
        progressFill.style.width = '100%';
        progressText.textContent = 'تمام شد! ' + (data.working_count || 0) + ' working configs.';
        toast('تمام شد! ' + (data.working_count || 0) + ' کانفیگ سالم پیدا شد.');
      }).catch(function (e2) {
        bestConfig.value = 'Error: ' + e2.message;
        toast('Failed: ' + e2.message);
      });
    });
  });

  function renderResult(r, container) {
    var div = document.createElement('div');
    div.className = 'result-item ' + (r.ok ? 'ok' : 'fail');
    var ping = Number.isFinite(r.latency_ms) ? r.latency_ms + 'ms' : '-';
    div.innerHTML =
      '<span class="status">' + (r.ok ? 'OK' : 'FAIL') + '</span>' +
      '<span class="info">' + (r.endpoint || r.config_name || '-') + '</span>' +
      '<span class="meta">ping ' + ping + ' | score ' + (r.score || 0) + '</span>';
    container.insertBefore(div, container.firstChild);
  }

  // --- Copy Best Config ---
  $('#copyBestBtn').addEventListener('click', async function () {
    var text = $('#bestConfig').value.trim();
    if (!text || text.startsWith('No working') || text.startsWith('Error')) {
      toast('No config to copy yet.');
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      toast('Config copied!');
    } catch (e) {
      toast('Auto-copy failed; select and copy manually.');
    }
  });

  // --- Load saved deploy config on page load ---
  fetch('/api/deploy-config').then(function (res) { return res.json(); }).then(function (data) {
    if (!data.ok || !data.config) return;
    var cfg = data.config;
    if (cfg.api_token_masked && !$('#cfToken').value.trim()) {
      $('#cfToken').placeholder = 'Saved: ' + cfg.api_token_masked;
    }
    if (cfg.account_id && !$('#cfAccountId').value.trim()) $('#cfAccountId').value = cfg.account_id;
    if (cfg.worker_name && !$('#workerName').value.trim()) $('#workerName').value = cfg.worker_name;
    if (cfg.uuid && !$('#bpbUuid').value.trim()) $('#bpbUuid').value = cfg.uuid;
    if (cfg.sub_path && !$('#subPath').value.trim()) $('#subPath').value = cfg.sub_path;
    if (cfg.proxy_ip && !$('#proxyIp').value.trim()) $('#proxyIp').value = cfg.proxy_ip;
    if (cfg.subscription_url && !$('#subUrl').value.trim()) $('#subUrl').value = cfg.subscription_url;
    // Load saved IPs
    if (data.saved_ips && !$('#ipList').value.trim()) $('#ipList').value = data.saved_ips;
  }).catch(function () {});

})();
