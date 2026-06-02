/* CoConection — Frontend Logic — NO eval, NO new Function */
(function () {
  'use strict';

  var $ = function (q) { return document.querySelector(q); };
  var $$ = function (q) { return Array.from(document.querySelectorAll(q)); };

  // ---- Theme Management ----
  var THEME_KEY = 'coconnection-theme';
  function getTheme() {
    try { return localStorage.getItem(THEME_KEY) || 'dark'; } catch (e) { return 'dark'; }
  }
  function setTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    try { localStorage.setItem(THEME_KEY, theme); } catch (e) {}
  }
  setTheme(getTheme());

  $('#themeToggle').addEventListener('click', function () {
    var current = document.body.getAttribute('data-theme');
    setTheme(current === 'dark' ? 'light' : 'dark');
  });

  // ---- Step Collapse ----
  $$('.step-toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var step = btn.closest('.step');
      step.classList.toggle('collapsed');
    });
  });

  // ---- Toast ----
  function toast(msg) {
    var t = $('#toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(function () { t.classList.remove('show'); }, 3500);
  }

  // ---- API Helpers ----
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

  // ---- Payload Builders ----
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

  // ---- UUID Generation ----
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
    toast('UUID ساخته شد!');
  });

  // ---- Cloudflare Verify ----
  $('#verifyCfBtn').addEventListener('click', async function () {
    var btn = this;
    btn.disabled = true;
    $('#cfResult').textContent = 'در حال بررسی توکن...';
    try {
      var data = await post('/api/cf-verify', cfPayload());
      var accounts = data.accounts || [];
      $('#cfResult').textContent = 'توکن معتبر است!\nاکانت‌ها:\n' +
        (accounts.map(function (a) { return '- ' + (a.name || 'Account') + ' | ' + a.id; }).join('\n') || 'اکانتی یافت نشد؛ Account ID را دستی وارد کن.');
      if (accounts.length && !$('#cfAccountId').value.trim()) {
        $('#cfAccountId').value = accounts[0].id;
      }
      toast('توکن تایید شد!');
    } catch (e) {
      $('#cfResult').textContent = 'خطا: ' + e.message;
      toast('تایید توکن ناموفق بود.');
    } finally { btn.disabled = false; }
  });

  // ---- Cloudflare Deploy ----
  $('#deployCfBtn').addEventListener('click', async function () {
    var btn = this;
    btn.disabled = true;
    $('#cfResult').textContent = 'در حال Deploy روی Cloudflare...';
    try {
      var data = await post('/api/cf-deploy', cfPayload());
      var lines = [data.ok ? 'Deploy موفق!' : 'Deploy ناموفق.'];
      if (data.worker_url_hint) {
        lines.push('');
        lines.push('Subscription URL:');
        lines.push(data.worker_url_hint);
        $('#subUrl').value = data.worker_url_hint;
      }
      if (data.next_steps_fa) {
        lines.push('');
        lines.push('مراحل بعدی:');
        data.next_steps_fa.forEach(function (x) { lines.push('- ' + x); });
      }
      $('#cfResult').textContent = lines.join('\n');
      toast('Deploy انجام شد!');
    } catch (e) {
      $('#cfResult').textContent = 'خطا: ' + e.message;
      toast('Deploy ناموفق بود.');
    } finally { btn.disabled = false; }
  });

  // ---- Paste ----
  $('#pasteBtn').addEventListener('click', async function () {
    try {
      $('#subUrl').value = await navigator.clipboard.readText();
      toast('از کلیپ‌بورد Paste شد.');
    } catch (e) { toast('Paste ناموفق؛ دستی Paste کن.'); }
  });

  // ---- Check Link ----
  $('#fetchBtn').addEventListener('click', async function () {
    var btn = this;
    btn.disabled = true;
    try {
      var data = await post('/api/fetch', runPayload());
      var msg = 'لینک OK!\nکل خطوط: ' + data.total_lines + '\nکانفیگ‌های پشتیبانی‌شده: ' + data.supported_configs;
      if (data.fetch_warning) msg = 'هشدار: ' + data.fetch_warning + '\n\n' + msg;
      if (data.examples && data.examples.length) {
        msg += '\nنمونه‌ها:\n- ' + data.examples.slice(0, 6).join('\n- ');
      }
      toast('Subscription دریافت شد!');
      $('#cfResult').textContent = msg;
    } catch (e) {
      toast('دریافت ناموفق: ' + e.message);
    } finally { btn.disabled = false; }
  });

  // ---- IP Scanner ----
  $('#scanIpBtn').addEventListener('click', async function () {
    var btn = this;
    btn.disabled = true;
    btn.textContent = 'Scanning...';
    $('#ipScanResult').textContent = 'اسکن شروع شد...';
    try {
      var data = await post('/api/scan-ips', scanPayload());
      var lines = ['کاندیدها: ' + data.candidate_count, 'Endpointهای سالم: ' + data.working_count, ''];
      (data.top_results || []).slice(0, 20).forEach(function (r) {
        lines.push((r.ok ? 'OK' : 'FAIL') + ' | ' + r.endpoint + ' | ' + r.latency_ms + 'ms | ' + (r.message || ''));
      });
      lines.push('\nذخیره شد: ' + (data.files && data.files.clean || 'output/clean_ips.txt'));
      $('#ipScanResult').textContent = lines.join('\n');
      if (data.clean_ips && data.clean_ips.length) {
        window._lastCleanIps = data.clean_ips;
      }
      toast(data.working_count + ' endpoint سالم پیدا شد!');
    } catch (e) {
      $('#ipScanResult').textContent = 'خطا: ' + e.message;
      toast('اسکن ناموفق بود.');
    } finally { btn.disabled = false; btn.textContent = 'Scan'; }
  });

  $('#useCleanIpsBtn').addEventListener('click', function () {
    if (!window._lastCleanIps || !window._lastCleanIps.length) {
      toast('اول اسکنر را اجرا کن.');
      return;
    }
    $('#ipList').value = window._lastCleanIps.join('\n');
    var cleanRadio = document.querySelector('input[name="mode"][value="clean_ip"]');
    if (cleanRadio) cleanRadio.checked = true;
    toast('IPهای سالم بارگذاری شد!');
  });

  // ---- Open Output ----
  $('#openOutputBtn').addEventListener('click', function () { fetch('/api/open-output'); });
  $('#openOutputBtn2').addEventListener('click', function () { fetch('/api/open-output'); });

  // ---- RUN with SSE streaming ----
  $('#runBtn').addEventListener('click', function () {
    var btn = this;
    btn.disabled = true;
    btn.querySelector('svg').style.animation = 'pulse 1s infinite';

    var progressDiv = $('#liveProgress');
    var progressFill = $('#progressFill');
    var progressText = $('#progressText');
    var resultsDiv = $('#results');
    var bestConfig = $('#bestConfig');

    progressDiv.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = 'در حال شروع...';
    resultsDiv.innerHTML = '';
    bestConfig.value = '';

    var totalExpected = 0;
    var doneCount = 0;
    var workingCount = 0;
    var allResults = [];

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
            btn.querySelector('svg').style.animation = '';
            return;
          }

          buffer += decoder.decode(result.value, { stream: true });
          var parts = buffer.split('\n\n');
          buffer = parts.pop() || '';

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
              progressText.textContent = data.message || 'در حال شروع...';
            }
            else if (eventType === 'phase') {
              progressText.textContent = data.message || 'در حال پردازش...';
            }
            else if (eventType === 'progress') {
              doneCount = data.done;
              totalExpected = data.total || totalExpected;
              if (totalExpected > 0) {
                progressFill.style.width = Math.round((doneCount / totalExpected) * 100) + '%';
              }
              progressText.textContent = 'تست ' + doneCount + '/' + totalExpected + ' — ' + (data.ok ? 'OK' : 'FAIL') + ' ' + data.endpoint;
              if (data.ok) workingCount++;
              allResults.push(data);
              renderResult(data, resultsDiv);
            }
            else if (eventType === 'done') {
              progressFill.style.width = '100%';
              progressText.textContent = 'تمام شد! ' + (data.working_count || 0) + ' کانفیگ سالم پیدا شد.';

              if (data.best && data.best.config) {
                bestConfig.value = data.best.config;
              } else if (data.working_count === 0) {
                bestConfig.value = 'کانفیگ سالم پیدا نشد. Deploy را چک کن یا دوباره Start را بزن.';
              }

              if (data.warnings && data.warnings.length) {
                toast('با هشدار تمام شد: ' + data.warnings[0]);
              } else {
                toast('تمام شد! ' + (data.working_count || 0) + ' کانفیگ سالم پیدا شد.');
              }

              if (data.top_results && data.top_results.length && allResults.length === 0) {
                data.top_results.forEach(function (r) { renderResult(r, resultsDiv); });
              }

              btn.disabled = false;
              btn.querySelector('svg').style.animation = '';
            }
          }
          return processChunk();
        });
      }
      return processChunk();
    }).catch(function (err) {
      progressText.textContent = 'خطا: ' + err.message;
      btn.disabled = false;
      btn.querySelector('svg').style.animation = '';
      toast('خطای اتصال. تلاش مجدد بدون streaming...');

      post('/api/run', payload).then(function (data) {
        if (data.best && data.best.config) {
          bestConfig.value = data.best.config;
        }
        if (data.top_results) {
          data.top_results.forEach(function (r) { renderResult(r, resultsDiv); });
        }
        progressFill.style.width = '100%';
        progressText.textContent = 'تمام شد! ' + (data.working_count || 0) + ' کانفیگ سالم.';
        toast('تمام شد! ' + (data.working_count || 0) + ' کانفیگ سالم پیدا شد.');
      }).catch(function (e2) {
        bestConfig.value = 'خطا: ' + e2.message;
        toast('ناموفق: ' + e2.message);
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

  // ---- Copy Best Config ----
  $('#copyBestBtn').addEventListener('click', async function () {
    var text = $('#bestConfig').value.trim();
    if (!text || text.startsWith('No working') || text.startsWith('Error') || text.startsWith('کانفیگ')) {
      toast('هنوز کانفیگی برای کپی نیست.');
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      toast('کانفیگ کپی شد!');
    } catch (e) {
      toast('کپی خودکار ناموفق؛ دستی کپی کن.');
    }
  });

  // ---- Custom Config Builder ----
  var customConfigsList = [];

  $('#buildCustomBtn').addEventListener('click', async function () {
    var savedConfig = await getDeployConfig();
    var uuid = savedConfig.uuid || $('#bpbUuid').value.trim();
    if (!uuid) {
      toast('اول UUID را وارد کن (مرحله ۱) یا Worker را Deploy کن.');
      return;
    }

    var subUrl = $('#subUrl').value.trim();
    var hostname = '';
    try {
      var parsed = new URL(subUrl);
      hostname = parsed.hostname;
    } catch (e) {
      // Try from saved config
      if (savedConfig.worker_name) {
        hostname = savedConfig.worker_name + '.workers.dev';
      }
    }
    if (!hostname) {
      toast('Subscription URL وارد کن یا Worker را Deploy کن.');
      return;
    }

    var name = $('#customConfigName').value.trim() || 'Custom';
    var volumeGB = parseInt($('#customVolumeGB').value || '0', 10);
    var expiryDays = parseInt($('#customExpiryDays').value || '0', 10);
    var protocol = $('#customProtocol').value;
    var port = $('#customPort').value;
    var network = $('#customNetwork').value;
    var sni = $('#customSni').value.trim() || hostname;
    var path = $('#customPath').value.trim() || '/' + uuid + '-vless';
    var cleanIp = $('#customCleanIp').value.trim() || hostname;

    // Generate a new UUID for the custom config
    var customUuid;
    if (crypto.randomUUID) {
      customUuid = crypto.randomUUID();
    } else {
      customUuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0;
        var v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      });
    }

    // Build name with volume/expiry info
    var displayParts = [name];
    if (volumeGB > 0) displayParts.push(volumeGB + 'GB');
    else displayParts.push('Unlimited');
    if (expiryDays > 0) displayParts.push(expiryDays + 'D');
    else displayParts.push('NoExpiry');
    var displayName = displayParts.join('-');

    // Build the config URL
    var configUrl = '';
    if (protocol === 'vless') {
      if (network === 'ws') {
        configUrl = 'vless://' + uuid + '@' + cleanIp + ':' + port +
          '?encryption=none&security=tls&sni=' + sni +
          '&type=ws&host=' + hostname +
          '&path=' + encodeURIComponent(path) +
          '#' + encodeURIComponent(displayName);
      } else {
        // gRPC
        configUrl = 'vless://' + uuid + '@' + cleanIp + ':' + port +
          '?encryption=none&security=tls&sni=' + sni +
          '&type=grpc&serviceName=' + uuid + '-grpc' +
          '&host=' + hostname +
          '#' + encodeURIComponent(displayName);
      }
    } else if (protocol === 'trojan') {
      configUrl = 'trojan://' + uuid + '@' + cleanIp + ':' + port +
        '?security=tls&sni=' + sni +
        '&type=ws&host=' + hostname +
        '&path=' + encodeURIComponent('/trojan/' + uuid) +
        '#' + encodeURIComponent(displayName);
    }

    if (!configUrl) {
      toast('ساخت کانفیگ ناموفق.');
      return;
    }

    // Show result
    var outputArea = $('#customOutputArea');
    outputArea.style.display = 'block';

    var badge = $('#customBadge');
    badge.textContent = protocol.toUpperCase() + '-' + network.toUpperCase() + '-' + port;

    var meta = $('#customMeta');
    var metaParts = [];
    metaParts.push(volumeGB > 0 ? volumeGB + ' GB' : 'حجم نامحدود');
    metaParts.push(expiryDays > 0 ? expiryDays + ' روز' : 'زمان نامحدود');
    meta.textContent = metaParts.join(' — ');

    $('#customConfigOutput').value = configUrl;
    customConfigsList.push(configUrl);

    toast('کانفیگ سفارشی ساخته شد!');
  });

  // ---- Copy Custom Config ----
  $('#copyCustomBtn').addEventListener('click', async function () {
    var text = $('#customConfigOutput').value.trim();
    if (!text) { toast('کانفیگی نیست.'); return; }
    try {
      await navigator.clipboard.writeText(text);
      toast('کانفیگ سفارشی کپی شد!');
    } catch (e) {
      toast('کپی ناموفق.');
    }
  });

  // ---- Add Custom to Output List ----
  $('#addToListBtn').addEventListener('click', function () {
    var text = $('#customConfigOutput').value.trim();
    if (!text) { toast('اول کانفیگ سفارشی بساز.'); return; }

    // Send to backend to save
    fetch('/api/save-custom-config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config: text })
    }).then(function (res) { return res.json(); }).then(function (data) {
      if (data.ok) {
        toast('کانفیگ سفارشی به لیست خروجی اضافه شد!');
      } else {
        toast('خطا در ذخیره.');
      }
    }).catch(function () {
      // Fallback: just add to best config textarea
      var bestConfig = $('#bestConfig');
      if (bestConfig.value.trim()) {
        bestConfig.value = text + '\n' + bestConfig.value;
      } else {
        bestConfig.value = text;
      }
      toast('کانفیگ سفارشی به خروجی اضافه شد.');
    });
  });

  // ---- Helper: Get Deploy Config ----
  async function getDeployConfig() {
    try {
      var res = await fetch('/api/deploy-config');
      var data = await res.json();
      return data.config || {};
    } catch (e) {
      return {};
    }
  }

  // ---- Load saved deploy config on page load ----
  fetch('/api/deploy-config').then(function (res) { return res.json(); }).then(function (data) {
    if (!data.ok || !data.config) return;
    var cfg = data.config;
    if (cfg.api_token_masked && !$('#cfToken').value.trim()) {
      $('#cfToken').placeholder = 'ذخیره شده: ' + cfg.api_token_masked;
    }
    if (cfg.account_id && !$('#cfAccountId').value.trim()) $('#cfAccountId').value = cfg.account_id;
    if (cfg.worker_name && !$('#workerName').value.trim()) $('#workerName').value = cfg.worker_name;
    if (cfg.uuid && !$('#bpbUuid').value.trim()) $('#bpbUuid').value = cfg.uuid;
    if (cfg.sub_path && !$('#subPath').value.trim()) $('#subPath').value = cfg.sub_path;
    if (cfg.proxy_ip && !$('#proxyIp').value.trim()) $('#proxyIp').value = cfg.proxy_ip;
    if (cfg.subscription_url && !$('#subUrl').value.trim()) $('#subUrl').value = cfg.subscription_url;
    if (data.saved_ips && !$('#ipList').value.trim()) $('#ipList').value = data.saved_ips;
  }).catch(function () {});

  // ---- Add pulse animation ----
  var style = document.createElement('style');
  style.textContent = '@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }';
  document.head.appendChild(style);

})();
