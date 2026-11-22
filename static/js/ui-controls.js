// MENING HUDUDIM - Global interface controls
// - makes content sections collapsible on every page
// - small / medium / large / auto display scale (persisted in localStorage)
// - collapses the side navigation panel

(function () {
    'use strict';

    const SCALE_KEY = 'mh-ui-scale';
    const COLLAPSIBLE_SELECTOR = [
        '.card', '.form-card', '.report-card', '.stats-card',
        '.content-panel', '.mh-section'
    ].join(', ');

    function applyScale(scale) {
        const root = document.documentElement;
        if (scale === 'auto') root.removeAttribute('data-ui-scale');
        else root.setAttribute('data-ui-scale', scale);

        document.querySelectorAll('[data-scale]').forEach(function (button) {
            button.classList.toggle('active', button.getAttribute('data-scale') === scale);
        });

        try { localStorage.setItem(SCALE_KEY, scale); } catch (err) { /* private mode */ }
        window.dispatchEvent(new Event('resize'));
    }

    // Every top-level block of a page becomes a collapsible section, so the
    // behaviour is identical on all pages regardless of their markup.
    function wrapPageSections() {
        const main = document.querySelector('.app-page-content');
        if (!main) return;

        Array.prototype.slice.call(main.children).forEach(function (block, index) {
            if (['SCRIPT', 'STYLE'].indexOf(block.tagName) !== -1) return;
            if (block.dataset.mhNoCollapse === '1') return;

            const heading = block.querySelector('h1, h2, h3, h4, h5, h6, .card-title, .section-title');
            const fallback = block.querySelector('.fw-bold, strong');
            let title = heading ? heading.textContent : (fallback ? fallback.textContent : '');
            title = title.replace(/\s+/g, ' ').trim();
            if (title.length > 48) title = title.slice(0, 48) + '…';
            if (!title) title = 'Bo‘lim ' + (index + 1);

            const wrap = document.createElement('section');
            wrap.className = 'mh-page-section mh-collapsible';

            const head = document.createElement('div');
            head.className = 'mh-page-section-head mh-head-wrap';
            head.setAttribute('role', 'button');
            head.setAttribute('tabindex', '0');
            head.setAttribute('aria-expanded', 'true');

            const label = document.createElement('span');
            label.textContent = title;
            const chevron = document.createElement('i');
            chevron.className = 'fa-solid fa-chevron-up mh-chevron ms-2';
            head.appendChild(label);
            head.appendChild(chevron);

            wrap.appendChild(head);
            main.insertBefore(wrap, block);
            wrap.appendChild(block);

            const toggle = function () {
                const collapsed = wrap.classList.toggle('is-collapsed');
                head.setAttribute('aria-expanded', String(!collapsed));
                updateSectionButton();
                window.dispatchEvent(new Event('resize'));
            };
            head.addEventListener('click', toggle);
            head.addEventListener('keydown', function (event) {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    toggle();
                }
            });
        });
    }

    function makeCollapsible() {
        document.querySelectorAll(COLLAPSIBLE_SELECTOR).forEach(function (el) {
            if (el.dataset.mhCollapsible === '1') return;
            if (el.closest('nav, footer, .accordion, .app-sidebar-desktop')) return;

            const header = el.querySelector(
                '.card-header, .card-title, .section-title, h1, h2, h3, h4, h5, h6'
            );
            if (!header) return;

            // The clickable header must be a direct child (or the only child of
            // a direct wrapper) so the rest of the section can be hidden safely.
            let headWrap = header;
            if (header.parentElement !== el) {
                const parent = header.parentElement;
                if (parent.parentElement === el && parent.children.length <= 3) {
                    headWrap = parent;
                } else {
                    return;
                }
            }

            el.classList.add('mh-collapsible');
            headWrap.classList.add('mh-head-wrap');
            header.classList.add('mh-section-head');
            header.setAttribute('role', 'button');
            header.setAttribute('tabindex', '0');
            header.setAttribute('aria-expanded', 'true');
            el.dataset.mhCollapsible = '1';

            const chevron = document.createElement('i');
            chevron.className = 'fa-solid fa-chevron-up mh-chevron ms-2';
            header.appendChild(chevron);

            const toggle = function (event) {
                if (event && event.target.closest('a, button, input, select, textarea, label')) return;
                const collapsed = el.classList.toggle('is-collapsed');
                header.setAttribute('aria-expanded', String(!collapsed));
                updateSectionButton();
                window.dispatchEvent(new Event('resize'));
            };

            header.addEventListener('click', toggle);
            header.addEventListener('keydown', function (event) {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    toggle();
                }
            });
        });
    }

    function updateSectionButton() {
        const button = document.querySelector('[data-mh-action="sections"]');
        if (!button) return;
        const sections = document.querySelectorAll('.mh-collapsible');
        const anyOpen = Array.prototype.some.call(sections, function (el) {
            return !el.classList.contains('is-collapsed');
        });
        const label = button.querySelector('.mh-action-label');
        if (label) label.textContent = anyOpen ? 'Hammasini yig‘ish' : 'Hammasini ochish';
        button.setAttribute('aria-pressed', String(anyOpen));
    }

    function toggleAllSections() {
        const sections = document.querySelectorAll('.mh-collapsible');
        if (!sections.length) return;
        const shouldCollapse = Array.prototype.some.call(sections, function (el) {
            return !el.classList.contains('is-collapsed');
        });
        sections.forEach(function (el) {
            el.classList.toggle('is-collapsed', shouldCollapse);
            el.querySelectorAll('.mh-section-head, .mh-page-section-head').forEach(function (head) {
                head.setAttribute('aria-expanded', String(!shouldCollapse));
            });
        });
        updateSectionButton();
        window.dispatchEvent(new Event('resize'));
    }

    function setSidebar(collapsed) {
        document.body.classList.toggle('sidebar-collapsed', collapsed);

        document.querySelectorAll('[data-sidebar-toggle]').forEach(function (button) {
            button.setAttribute('aria-expanded', String(!collapsed));
            const icon = button.querySelector('i');
            if (icon) icon.className = collapsed ? 'fa-solid fa-bars' : 'fa-solid fa-chevron-left';
        });

        const reopen = document.getElementById('sidebarReopen');
        if (reopen) {
            reopen.classList.toggle('d-none', !collapsed);
            reopen.setAttribute('aria-expanded', String(collapsed));
        }

        const toolButton = document.querySelector('[data-mh-action="sidebar"]');
        if (toolButton) {
            toolButton.classList.toggle('active', collapsed);
            const label = toolButton.querySelector('.mh-action-label');
            if (label) label.textContent = collapsed ? 'Ochish' : 'Yopish';
        }

        try { localStorage.setItem('mh-sidebar-collapsed', collapsed ? '1' : '0'); } catch (err) { /* ignore */ }
        window.dispatchEvent(new Event('resize'));
    }

    function initSidebar() {
        document.querySelectorAll('[data-sidebar-toggle]').forEach(function (button) {
            button.addEventListener('click', function () {
                setSidebar(!document.body.classList.contains('sidebar-collapsed'));
            });
        });
        let saved = '0';
        try { saved = localStorage.getItem('mh-sidebar-collapsed') || '0'; } catch (err) { /* ignore */ }
        if (saved === '1') setSidebar(true);
    }

    // One floating button opens ONE panel that holds all view controls:
    // section collapse, size modes and the side navigation toggle.
    function setControlPanel(open) {
        const panel = document.getElementById('mh-control-panel');
        const toggle = document.getElementById('mh-control-toggle');
        if (!panel || !toggle) return;
        panel.classList.toggle('d-none', !open);
        toggle.setAttribute('aria-expanded', String(open));
    }

    function buildToolbar() {
        const dock = document.createElement('div');
        dock.className = 'mh-control-dock';
        dock.innerHTML = [
            '<button type="button" class="mh-control-toggle" id="mh-control-toggle" ',
            '  aria-expanded="false" aria-controls="mh-control-panel" ',
            '  title="Ko‘rinish sozlamalari" aria-label="Ko‘rinish sozlamalari">',
            '  <i class="fa-solid fa-sliders"></i></button>',
            '<div class="mh-control-panel d-none" id="mh-control-panel">',
            '  <div class="mh-control-head">',
            '    <span><i class="fa-solid fa-sliders me-2"></i>Ko‘rinish sozlamalari</span>',
            '    <button type="button" class="mh-control-close" data-mh-close aria-label="Yopish">',
            '      <i class="fa-solid fa-xmark"></i></button>',
            '  </div>',
            '  <div class="mh-control-row">',
            '    <span class="mh-control-label"><i class="fa-solid fa-layer-group me-2"></i>Bo‘limlar</span>',
            '    <button type="button" class="mh-control-action" data-mh-action="sections" aria-pressed="false">',
            '      <span class="mh-action-label">Hammasini yig‘ish</span></button>',
            '  </div>',
            '  <div class="mh-control-row mh-control-row-scale">',
            '    <span class="mh-control-label"><i class="fa-solid fa-text-height me-2"></i>O‘lcham</span>',
            '    <div class="mh-ui-scales">',
            '      <button type="button" class="mh-ui-scale-btn" data-scale="sm" ',
            '        title="Kichik ko‘rinish"><i class="fa-solid fa-compress"></i>',
            '        <span class="mh-scale-label">Kichik</span></button>',
            '      <button type="button" class="mh-ui-scale-btn" data-scale="md" ',
            '        title="O‘rtacha ko‘rinish"><i class="fa-solid fa-minus"></i>',
            '        <span class="mh-scale-label">O‘rta</span></button>',
            '      <button type="button" class="mh-ui-scale-btn" data-scale="lg" ',
            '        title="Katta ko‘rinish"><i class="fa-solid fa-expand"></i>',
            '        <span class="mh-scale-label">Katta</span></button>',
            '      <button type="button" class="mh-ui-scale-btn" data-scale="auto" ',
            '        title="Avtomatik moslash"><i class="fa-solid fa-wand-magic-sparkles"></i>',
            '        <span class="mh-scale-label">Avto</span></button>',
            '    </div>',
            '  </div>',
            '  <div class="mh-control-row">',
            '    <span class="mh-control-label"><i class="fa-solid fa-panel-left me-2"></i>Yon panel</span>',
            '    <button type="button" class="mh-control-action" data-mh-action="sidebar">',
            '      <span class="mh-action-label">Yopish</span></button>',
            '  </div>',
            '</div>'
        ].join('');
        document.body.appendChild(dock);

        dock.addEventListener('click', function (event) {
            if (event.target.closest('#mh-control-toggle')) {
                setControlPanel(document.getElementById('mh-control-panel').classList.contains('d-none'));
                return;
            }
            if (event.target.closest('[data-mh-close]')) {
                setControlPanel(false);
                return;
            }

            const scaleBtn = event.target.closest('[data-scale]');
            if (scaleBtn) {
                applyScale(scaleBtn.getAttribute('data-scale'));
                return;
            }
            const actionBtn = event.target.closest('[data-mh-action]');
            if (!actionBtn) return;

            if (actionBtn.getAttribute('data-mh-action') === 'sections') {
                toggleAllSections();
            } else if (actionBtn.getAttribute('data-mh-action') === 'sidebar') {
                setSidebar(!document.body.classList.contains('sidebar-collapsed'));
            }
            // Keep the single control panel open so the result is visible immediately.
        });

        document.addEventListener('click', function (event) {
            if (!dock.contains(event.target)) setControlPanel(false);
        });
        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') setControlPanel(false);
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        let saved = 'auto';
        try { saved = localStorage.getItem(SCALE_KEY) || 'auto'; } catch (err) { /* ignore */ }
        if (['sm', 'md', 'lg', 'auto'].indexOf(saved) === -1) saved = 'auto';

        buildToolbar();
        initSidebar();
        wrapPageSections();
        makeCollapsible();
        updateSectionButton();
        applyScale(saved);
    });
})();
