(() => {
  const MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"];
  const MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];
  const DAYS = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"];
  let uid = 0;
  const nextId = (prefix) => `${prefix}-${++uid}`;
  const el = (tag, attrs = {}, children = []) => {
    const node = document.createElement(tag);
    Object.entries(attrs).forEach(([key, value]) => {
      if (value === null || value === undefined || value === false) return;
      if (key === "class") node.className = value;
      else if (key === "text") node.textContent = value;
      else node.setAttribute(key, value === true ? "" : value);
    });
    [].concat(children).forEach((child) => child && node.append(child));
    return node;
  };
  const icon = (path) => {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("class", "icon");
    svg.setAttribute("aria-hidden", "true");
    svg.innerHTML = path;
    return svg;
  };
  const ICONS = {
    calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18"/>',
    upload: '<path d="M12 16V4M7 9l5-5 5 5"/><path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/>',
    left: '<path d="M15 18l-6-6 6-6"/>',
    right: '<path d="M9 18l6-6-6-6"/>',
    close: '<path d="M18 6 6 18M6 6l12 12"/>',
    alert: '<circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/>'
  };
  const fieldOf = (input) => input.closest(".field");
  const labelOf = (input) => {
    if (input.type === "radio" || input.type === "checkbox") {
      const legend = input.closest("fieldset")?.querySelector("legend");
      if (legend) return legend.textContent.trim();
    }
    const field = fieldOf(input);
    const label = (input.id && document.querySelector(`label[for="${CSS.escape(input.id)}"]`)) || (field && field.querySelector(".field__label"));
    return label ? (label.querySelector("[data-label-text]") || label).textContent.replace(/\*|\(opsional\)/g, "").trim() : input.name;
  };
  const placeAbove = (anchor, height) => {
    const rect = anchor.getBoundingClientRect();
    return window.innerHeight - rect.bottom < height && rect.top > height;
  };

  const toastRoot = () => document.querySelector(".toasts") || document.body.appendChild(el("div", { class: "toasts", role: "region", "aria-live": "polite", "aria-label": "Notifikasi" }));
  const toast = (message, kind = "success", timeout = 4200) => {
    const close = el("button", { class: "toast__close", type: "button", "aria-label": "Tutup notifikasi", text: "×" });
    const node = el("div", { class: `toast toast--${kind}`, role: kind === "danger" ? "alert" : "status" }, [el("span", { class: "toast__icon", "aria-hidden": "true" }), el("div", { text: message }), close]);
    const remove = () => {
      node.classList.add("is-leaving");
      setTimeout(() => node.remove(), 260);
    };
    close.addEventListener("click", remove);
    toastRoot().append(node);
    if (timeout) setTimeout(remove, timeout);
    return node;
  };

  const setError = (input, message) => {
    const field = fieldOf(input);
    if (!field) return;
    let error = field.querySelector(".field__error");
    if (!error) {
      error = el("p", { class: "field__error", id: nextId("err") });
      field.append(error);
    }
    if (message) {
      error.replaceChildren(icon(ICONS.alert), document.createTextNode(message));
      field.classList.add("is-invalid");
      input.setAttribute("aria-invalid", "true");
      input.setAttribute("aria-describedby", [input.getAttribute("aria-describedby"), error.id].filter(Boolean).join(" "));
    } else {
      field.classList.remove("is-invalid");
      input.removeAttribute("aria-invalid");
    }
  };
  const messageFor = (input) => {
    if (input.dataset.error) return input.dataset.error;
    const v = input.validity;
    if (v.valueMissing) return input.type === "file" ? "Pilih minimal satu file." : input.tagName === "SELECT" ? "Pilih salah satu opsi." : "Wajib diisi.";
    if (v.typeMismatch && input.type === "email") return "Format email belum benar, contoh: nama@kantor.go.id";
    if (v.tooShort) return `Minimal ${input.minLength} karakter.`;
    if (v.tooLong) return `Maksimal ${input.maxLength} karakter.`;
    if (v.patternMismatch) return input.title || "Format belum sesuai.";
    if (v.rangeUnderflow) return `Minimal ${input.min}.`;
    if (v.rangeOverflow) return `Maksimal ${input.max}.`;
    return input.validationMessage;
  };
  const validate = (scope) => {
    let first = null;
    scope.querySelectorAll("input, select, textarea").forEach((input) => {
      if (input.disabled || input.type === "hidden" || input.closest("[hidden]") && !input.closest(".combo, .upload")) return;
      const ok = input.checkValidity();
      setError(input, ok ? "" : messageFor(input));
      if (!ok && !first) first = input;
    });
    if (first) {
      const target = first.closest(".combo")?.querySelector("[role=combobox]") || first.closest(".upload")?.querySelector(".upload__zone") || first.closest(".datepicker")?.querySelector(".input") || first;
      target.focus({ preventScroll: true });
      target.scrollIntoView({ block: "center", behavior: "smooth" });
    }
    return !first;
  };

  const initCounter = (input) => {
    const field = fieldOf(input);
    const label = field && field.querySelector(".field__label");
    if (!label || !input.maxLength || input.maxLength < 0) return;
    const counter = el("span", { class: "field__counter", "aria-live": "polite" });
    label.append(counter);
    const update = () => {
      const left = input.maxLength - input.value.length;
      counter.textContent = `${input.value.length}/${input.maxLength}`;
      counter.classList.toggle("is-near", left <= Math.max(10, input.maxLength * 0.1) && left > 0);
      counter.classList.toggle("is-over", left <= 0);
    };
    input.addEventListener("input", update);
    update();
  };

  const initCombo = (select) => {
    const multi = select.multiple;
    const wrap = el("div", { class: `combo ${multi ? "combo--multi" : "combo--single"}` });
    select.parentNode.insertBefore(wrap, select);
    wrap.append(select);
    select.classList.add("combo__native");
    select.tabIndex = -1;
    select.setAttribute("aria-hidden", "true");
    const listId = nextId("list");
    const labelText = labelOf(select);
    const placeholder = select.dataset.placeholder || (multi ? "Pilih satu atau lebih" : "Pilih...");
    const control = el("div", { class: "combo__control" });
    const list = el("ul", { class: "combo__list", id: listId, role: "listbox", "aria-label": labelText, "aria-multiselectable": multi ? "true" : null });
    const panel = el("div", { class: "combo__panel" });
    const options = Array.from(select.options).filter((o) => o.value !== "" || multi);
    const searchable = multi || select.dataset.search === "true" || options.length > 7;
    let focusTarget;
    let filter = null;
    if (multi) {
      focusTarget = el("input", { class: "combo__search", type: "text", role: "combobox", "aria-expanded": "false", "aria-controls": listId, "aria-autocomplete": "list", "aria-label": labelText, placeholder, autocomplete: "off" });
      control.append(focusTarget);
    } else {
      focusTarget = control;
      control.setAttribute("role", "combobox");
      control.setAttribute("tabindex", "0");
      control.setAttribute("aria-expanded", "false");
      control.setAttribute("aria-controls", listId);
      control.setAttribute("aria-haspopup", "listbox");
      control.setAttribute("aria-label", labelText);
      control.append(el("span", { class: "combo__value" }));
      if (searchable) {
        filter = el("input", { class: "combo__filter", type: "text", placeholder: "Cari...", "aria-label": `Cari ${labelText}`, "aria-controls": listId, autocomplete: "off" });
        panel.append(filter);
      }
    }
    if (select.id) {
      const label = document.querySelector(`label[for="${CSS.escape(select.id)}"]`);
      if (label) label.addEventListener("click", (e) => { e.preventDefault(); focusTarget.focus(); });
    }
    panel.append(list);
    let countNode = null;
    if (multi) {
      countNode = el("span");
      const all = el("button", { class: "combo__link", type: "button", text: "Pilih semua" });
      const clear = el("button", { class: "combo__link", type: "button", text: "Hapus" });
      all.addEventListener("click", () => { visibleOptions().forEach((o) => { if (!o.disabled) o.selected = true; }); commit(); });
      clear.addEventListener("click", () => { options.forEach((o) => { o.selected = false; }); commit(); focusTarget.focus(); });
      panel.append(el("div", { class: "combo__foot" }, [countNode, el("span", { class: "btn-group" }, [all, clear])]));
    }
    wrap.append(control, panel);
    let active = -1;
    let rendered = [];
    const query = () => (multi ? focusTarget.value : filter ? filter.value : "").trim().toLowerCase();
    const visibleOptions = () => options.filter((o) => o.text.toLowerCase().includes(query()));
    const renderList = () => {
      list.replaceChildren();
      rendered = [];
      let group = null;
      visibleOptions().forEach((option) => {
        const parent = option.parentElement.tagName === "OPTGROUP" ? option.parentElement.label : null;
        if (parent !== group && parent) list.append(el("li", { class: "combo__group", role: "presentation", text: parent }));
        group = parent;
        const id = nextId("opt");
        const item = el("li", { class: "combo__option", id, role: "option", "aria-selected": String(option.selected), "aria-disabled": option.disabled ? "true" : null }, [
          el("span", { class: "combo__check", "aria-hidden": "true" }),
          el("span", {}, [document.createTextNode(option.text), option.dataset.desc ? el("span", { class: "combo__option-desc", text: option.dataset.desc }) : null])
        ]);
        item.addEventListener("mousedown", (e) => e.preventDefault());
        item.addEventListener("click", () => choose(option));
        list.append(item);
        rendered.push({ option, item });
      });
      if (!rendered.length) list.append(el("li", { class: "combo__empty", role: "presentation", text: "Tidak ada hasil" }));
      active = Math.min(active, rendered.length - 1);
      highlight();
    };
    const highlight = () => {
      rendered.forEach(({ item }, i) => item.classList.toggle("is-active", i === active));
      const current = rendered[active];
      const owner = filter || focusTarget;
      if (current) {
        owner.setAttribute("aria-activedescendant", current.item.id);
        current.item.scrollIntoView({ block: "nearest" });
      } else owner.removeAttribute("aria-activedescendant");
    };
    const renderValue = () => {
      const selected = options.filter((o) => o.selected);
      if (multi) {
        control.querySelectorAll(".chip").forEach((c) => c.remove());
        const max = Number(select.dataset.maxChips || 3);
        selected.slice(0, max).forEach((option) => {
          const remove = el("button", { class: "chip__remove", type: "button", "aria-label": `Hapus ${option.text}`, text: "×" });
          remove.addEventListener("mousedown", (e) => e.preventDefault());
          remove.addEventListener("click", (e) => { e.stopPropagation(); option.selected = false; commit(); });
          control.insertBefore(el("span", { class: "chip" }, [el("span", { class: "chip__label", text: option.text }), remove]), focusTarget);
        });
        if (selected.length > max) control.insertBefore(el("span", { class: "chip chip--more", text: `+${selected.length - max}` }), focusTarget);
        focusTarget.placeholder = selected.length ? "" : placeholder;
        countNode.textContent = `${selected.length} dipilih`;
      } else {
        const value = control.querySelector(".combo__value");
        const option = selected.find((o) => o.value !== "");
        value.textContent = option ? option.text : placeholder;
        value.classList.toggle("is-placeholder", !option);
      }
    };
    const commit = () => {
      renderValue();
      renderList();
      select.dispatchEvent(new Event("change", { bubbles: true }));
      if (select.checkValidity()) setError(select, "");
    };
    const choose = (option) => {
      if (option.disabled) return;
      if (multi) {
        option.selected = !option.selected;
        focusTarget.value = "";
        commit();
        focusTarget.focus();
      } else {
        option.selected = true;
        commit();
        close();
        control.focus();
      }
    };
    const open = () => {
      if (wrap.classList.contains("is-open")) return;
      document.querySelectorAll(".combo.is-open, .datepicker.is-open").forEach((o) => o !== wrap && o.dispatchEvent(new CustomEvent("ui:close")));
      wrap.classList.toggle("is-up", placeAbove(control, 320));
      wrap.classList.add("is-open");
      focusTarget.setAttribute("aria-expanded", "true");
      active = Math.max(0, rendered.findIndex(({ option }) => option.selected));
      renderList();
      if (filter) { filter.value = ""; renderList(); filter.focus(); }
    };
    const close = () => {
      wrap.classList.remove("is-open");
      focusTarget.setAttribute("aria-expanded", "false");
      if (filter) filter.value = "";
      if (multi) focusTarget.value = "";
      active = -1;
      renderList();
    };
    wrap.addEventListener("ui:close", close);
    const keys = (e) => {
      const isOpen = wrap.classList.contains("is-open");
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        if (!isOpen) return open();
        active = (active + (e.key === "ArrowDown" ? 1 : -1) + rendered.length) % Math.max(rendered.length, 1);
        highlight();
      } else if (e.key === "Enter" || (e.key === " " && e.target === control)) {
        e.preventDefault();
        if (!isOpen) return open();
        if (rendered[active]) choose(rendered[active].option);
      } else if (e.key === "Escape" && isOpen) {
        e.preventDefault();
        close();
        focusTarget.focus();
      } else if (e.key === "Tab" && isOpen) {
        close();
      } else if (e.key === "Backspace" && multi && !focusTarget.value) {
        const last = options.filter((o) => o.selected).pop();
        if (last) { last.selected = false; commit(); }
      }
    };
    focusTarget.addEventListener("keydown", keys);
    if (filter) {
      filter.addEventListener("keydown", keys);
      filter.addEventListener("input", () => { active = 0; renderList(); });
    }
    if (multi) {
      focusTarget.addEventListener("input", () => { open(); active = 0; renderList(); });
      focusTarget.addEventListener("focus", open);
    }
    control.addEventListener("click", (e) => {
      if (e.target.closest(".chip__remove")) return;
      if (multi) { focusTarget.focus(); open(); return; }
      wrap.classList.contains("is-open") ? close() : open();
    });
    document.addEventListener("pointerdown", (e) => { if (!wrap.contains(e.target)) close(); });
    select.form && select.form.addEventListener("reset", () => setTimeout(() => { renderValue(); renderList(); }));
    select.addEventListener("ui:refresh", () => { renderValue(); renderList(); });
    renderValue();
    renderList();
  };

  const pad = (n) => String(n).padStart(2, "0");
  const toIso = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const fromIso = (s) => {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || "");
    if (!m) return null;
    const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
    return d.getMonth() === Number(m[2]) - 1 ? d : null;
  };
  const display = (d) => `${d.getDate()} ${MONTHS_SHORT[d.getMonth()]} ${d.getFullYear()}`;
  const parseTyped = (s) => {
    const t = s.trim().toLowerCase();
    let m = /^(\d{1,2})[\/\-. ](\d{1,2})[\/\-. ](\d{4})$/.exec(t);
    if (m) {
      const d = new Date(Number(m[3]), Number(m[2]) - 1, Number(m[1]));
      return d.getMonth() === Number(m[2]) - 1 ? d : null;
    }
    m = /^(\d{1,2}) ([a-z]+) (\d{4})$/.exec(t);
    if (m) {
      const idx = MONTHS.findIndex((name, i) => name.toLowerCase().startsWith(m[2].slice(0, 3)) || MONTHS_SHORT[i].toLowerCase() === m[2]);
      if (idx >= 0) return new Date(Number(m[3]), idx, Number(m[1]));
    }
    return fromIso(t);
  };
  const sameDay = (a, b) => a && b && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();

  const initDate = (native) => {
    const wrap = el("div", { class: "datepicker" });
    native.parentNode.insertBefore(wrap, native);
    const hidden = el("input", { type: "hidden", name: native.name, value: native.value });
    const visible = el("input", {
      class: "input", type: "text", id: native.id || nextId("date"), inputmode: "numeric", autocomplete: "off",
      placeholder: native.placeholder || "dd/mm/yyyy", required: native.required, "aria-describedby": native.getAttribute("aria-describedby"),
      "data-draft-target": native.name
    });
    const min = fromIso(native.min);
    const max = fromIso(native.max);
    const trigger = el("button", { class: "datepicker__trigger", type: "button", "aria-label": "Buka kalender", "aria-haspopup": "dialog", "aria-expanded": "false" }, [icon(ICONS.calendar)]);
    const title = el("span", { class: "datepicker__title", "aria-live": "polite" });
    const prev = el("button", { class: "datepicker__nav", type: "button", "aria-label": "Bulan sebelumnya" }, [icon(ICONS.left)]);
    const next = el("button", { class: "datepicker__nav", type: "button", "aria-label": "Bulan berikutnya" }, [icon(ICONS.right)]);
    const grid = el("table", { class: "datepicker__grid", role: "grid" });
    const today = el("button", { class: "combo__link", type: "button", text: "Hari ini" });
    const clear = el("button", { class: "combo__link", type: "button", text: "Hapus" });
    const panel = el("div", { class: "datepicker__panel", role: "dialog", "aria-modal": "false", "aria-label": `Pilih ${labelOf(native)}` }, [
      el("div", { class: "datepicker__head" }, [prev, title, next]), grid, el("div", { class: "datepicker__foot" }, [today, clear])
    ]);
    native.remove();
    wrap.append(hidden, visible, trigger, panel);
    let selected = fromIso(hidden.value);
    let cursor = selected ? new Date(selected) : new Date();
    const disabled = (d) => (min && d < min) || (max && d > max);
    const sync = () => {
      hidden.value = selected ? toIso(selected) : "";
      visible.value = selected ? display(selected) : "";
      hidden.dispatchEvent(new Event("change", { bubbles: true }));
      visible.dispatchEvent(new Event("input", { bubbles: true }));
      if (visible.checkValidity()) setError(visible, "");
    };
    const render = (focus) => {
      title.textContent = `${MONTHS[cursor.getMonth()]} ${cursor.getFullYear()}`;
      const first = new Date(cursor.getFullYear(), cursor.getMonth(), 1);
      const start = new Date(first);
      start.setDate(1 - ((first.getDay() + 6) % 7));
      const head = el("tr", {}, DAYS.map((d) => el("th", { scope: "col", text: d })));
      const body = el("tbody");
      const now = new Date();
      for (let w = 0; w < 6; w++) {
        const row = el("tr");
        for (let i = 0; i < 7; i++) {
          const d = new Date(start);
          d.setDate(start.getDate() + w * 7 + i);
          const cls = ["datepicker__day", d.getMonth() !== cursor.getMonth() && "is-outside", sameDay(d, now) && "is-today"].filter(Boolean).join(" ");
          const btn = el("button", { class: cls, type: "button", tabindex: sameDay(d, cursor) ? "0" : "-1", "aria-selected": sameDay(d, selected) ? "true" : "false", "aria-label": `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`, disabled: disabled(d), "data-iso": toIso(d), text: String(d.getDate()) });
          row.append(el("td", { role: "gridcell" }, [btn]));
        }
        body.append(row);
      }
      grid.replaceChildren(el("thead", {}, [head]), body);
      if (focus) grid.querySelector('[tabindex="0"]')?.focus();
    };
    const open = () => {
      document.querySelectorAll(".combo.is-open, .datepicker.is-open").forEach((o) => o !== wrap && o.dispatchEvent(new CustomEvent("ui:close")));
      cursor = selected ? new Date(selected) : new Date();
      wrap.classList.toggle("is-up", placeAbove(visible, 380));
      wrap.classList.add("is-open");
      trigger.setAttribute("aria-expanded", "true");
      render(true);
    };
    const close = (refocus) => {
      wrap.classList.remove("is-open");
      trigger.setAttribute("aria-expanded", "false");
      if (refocus) visible.focus();
    };
    wrap.addEventListener("ui:close", () => close(false));
    trigger.addEventListener("click", () => (wrap.classList.contains("is-open") ? close(true) : open()));
    visible.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown" && e.altKey) { e.preventDefault(); open(); }
    });
    visible.addEventListener("change", () => {
      if (!visible.value.trim()) { selected = null; sync(); return; }
      const parsed = parseTyped(visible.value);
      if (parsed && !disabled(parsed)) { selected = parsed; sync(); }
      else setError(visible, "Tanggal tidak dikenali atau di luar rentang. Contoh: 17/08/2026");
    });
    visible.addEventListener("ui:set", (e) => { selected = fromIso(e.detail); sync(); });
    prev.addEventListener("click", () => { cursor.setMonth(cursor.getMonth() - 1, 1); render(false); });
    next.addEventListener("click", () => { cursor.setMonth(cursor.getMonth() + 1, 1); render(false); });
    today.addEventListener("click", () => { const d = new Date(); if (!disabled(d)) { selected = d; sync(); close(true); } });
    clear.addEventListener("click", () => { selected = null; sync(); close(true); });
    grid.addEventListener("click", (e) => {
      const btn = e.target.closest(".datepicker__day");
      if (!btn || btn.disabled) return;
      selected = fromIso(btn.dataset.iso);
      sync();
      close(true);
    });
    grid.addEventListener("keydown", (e) => {
      const moves = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
      if (e.key in moves) { e.preventDefault(); cursor.setDate(cursor.getDate() + moves[e.key]); render(true); }
      else if (e.key === "PageUp" || e.key === "PageDown") { e.preventDefault(); cursor.setMonth(cursor.getMonth() + (e.key === "PageUp" ? -1 : 1)); render(true); }
      else if (e.key === "Home") { e.preventDefault(); cursor.setDate(cursor.getDate() - ((cursor.getDay() + 6) % 7)); render(true); }
      else if (e.key === "End") { e.preventDefault(); cursor.setDate(cursor.getDate() + (6 - ((cursor.getDay() + 6) % 7))); render(true); }
    });
    panel.addEventListener("keydown", (e) => { if (e.key === "Escape") { e.preventDefault(); close(true); } });
    document.addEventListener("pointerdown", (e) => { if (!wrap.contains(e.target)) close(false); });
    if (selected) visible.value = display(selected);
    if (hidden.form) hidden.form.addEventListener("reset", () => setTimeout(() => { selected = fromIso(hidden.value); visible.value = selected ? display(selected) : ""; }));
  };

  const formatSize = (bytes) => (bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1).replace(".", ",")} MB`);
  const accepts = (file, accept) => {
    if (!accept) return true;
    return accept.split(",").map((a) => a.trim().toLowerCase()).some((rule) => {
      if (rule.startsWith(".")) return file.name.toLowerCase().endsWith(rule);
      if (rule.endsWith("/*")) return file.type.startsWith(rule.slice(0, -1));
      return file.type === rule;
    });
  };

  const initUpload = (input) => {
    const wrap = el("div", { class: "upload" });
    input.parentNode.insertBefore(wrap, input);
    input.classList.add("upload__native");
    input.tabIndex = -1;
    const maxMb = Number(input.dataset.maxMb || 5);
    const maxFiles = Number(input.dataset.maxFiles || (input.multiple ? 10 : 1));
    const kinds = (input.accept || "").split(",").map((a) => a.trim()).filter(Boolean).map((a) => a === "image/*" ? "gambar" : a.startsWith(".") ? a.slice(1).toUpperCase() : (a.split("/")[1] || a).toUpperCase().replace("JPEG", "JPG"));
    const hint = input.dataset.hint || [kinds.join(", "), `maks. ${maxMb} MB${input.multiple ? ` per file, hingga ${maxFiles} file` : ""}`].filter(Boolean).join(" · ");
    const zone = el("div", { class: "upload__zone", role: "button", tabindex: "0", "aria-label": `${labelOf(input)}: ${input.multiple ? "pilih file" : "pilih satu file"} atau tarik ke sini` }, [
      el("span", { class: "upload__badge", "aria-hidden": "true" }, [icon(ICONS.upload)]),
      el("span", { class: "upload__title" }, [document.createTextNode("Tarik file ke sini atau "), el("u", { text: "pilih dari perangkat" })]),
      el("span", { class: "upload__meta", text: hint })
    ]);
    const list = el("ul", { class: "upload__list", "aria-live": "polite" });
    wrap.append(input, zone, list);
    let files = [];
    const syncNative = () => {
      const dt = new DataTransfer();
      files.filter((f) => !f.error).forEach((f) => dt.items.add(f.file));
      input.files = dt.files;
      input.dispatchEvent(new Event("change", { bubbles: true }));
      if (input.checkValidity()) setError(input, "");
    };
    const render = () => {
      list.replaceChildren(...files.map((entry, index) => {
        const ext = entry.file.name.split(".").pop().slice(0, 4);
        const thumb = el("span", { class: "upload__thumb", text: entry.preview ? "" : ext });
        if (entry.preview) thumb.style.backgroundImage = `url("${entry.preview}")`;
        const remove = el("button", { class: "btn btn--quiet btn--icon", type: "button", "aria-label": `Hapus ${entry.file.name}` }, [icon(ICONS.close)]);
        remove.addEventListener("click", () => {
          if (entry.preview) URL.revokeObjectURL(entry.preview);
          files.splice(index, 1);
          render();
          syncNative();
          zone.focus();
        });
        return el("li", { class: `upload__item${entry.error ? " is-error" : ""}` }, [
          thumb,
          el("span", { class: "upload__info" }, [el("span", { class: "upload__name", text: entry.file.name }), el("span", { class: "upload__size", text: entry.error || formatSize(entry.file.size) })]),
          remove
        ]);
      }));
    };
    const add = (incoming) => {
      const fresh = Array.from(incoming).map((file) => {
        let error = "";
        if (!accepts(file, input.accept)) error = "Jenis file tidak didukung";
        else if (file.size > maxMb * 1024 * 1024) error = `${formatSize(file.size)}, melebihi batas ${maxMb} MB`;
        return { file, error, preview: !error && file.type.startsWith("image/") ? URL.createObjectURL(file) : "" };
      });
      files = input.multiple ? files.concat(fresh) : fresh.slice(0, 1);
      const valid = files.filter((f) => !f.error);
      if (valid.length > maxFiles) {
        valid.slice(maxFiles).forEach((f) => { f.error = `Melebihi batas ${maxFiles} file`; });
      }
      render();
      syncNative();
    };
    zone.addEventListener("click", () => input.click());
    zone.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); } });
    input.addEventListener("change", (e) => { if (e.isTrusted && input.files.length) add(input.files); });
    ["dragenter", "dragover"].forEach((type) => zone.addEventListener(type, (e) => { e.preventDefault(); wrap.classList.add("is-dragging"); }));
    ["dragleave", "drop"].forEach((type) => zone.addEventListener(type, (e) => { e.preventDefault(); wrap.classList.remove("is-dragging"); }));
    zone.addEventListener("drop", (e) => add(e.dataTransfer.files));
    input.form && input.form.addEventListener("reset", () => { files = []; render(); });
    wrap.addEventListener("ui:add-files", (e) => add(e.detail));
  };

  const initForm = (form) => {
    form.noValidate = true;
    const bar = form.querySelector(".form-actions");
    const status = bar && bar.querySelector(".form-actions__text");
    const key = form.dataset.draftKey ? `draft:${form.dataset.draftKey}` : null;
    let dirty = false;
    let timer = null;
    const setState = (state, text) => {
      if (!bar) return;
      bar.dataset.state = state;
      if (status) status.textContent = text;
    };
    const snapshot = () => {
      const data = {};
      Array.from(form.elements).forEach((f) => {
        if (!f.name || ["file", "password", "submit", "button"].includes(f.type) || f.closest("[data-no-draft]")) return;
        if (f.type === "checkbox" || f.type === "radio") { if (f.checked) (data[f.name] = data[f.name] || []).push(f.value); }
        else if (f.multiple) data[f.name] = Array.from(f.selectedOptions).map((o) => o.value);
        else data[f.name] = f.value;
      });
      return data;
    };
    const restore = (data) => {
      Array.from(form.elements).forEach((f) => {
        if (!f.name || !(f.name in data)) return;
        const v = data[f.name];
        if (f.type === "checkbox" || f.type === "radio") f.checked = [].concat(v).includes(f.value);
        else if (f.multiple) Array.from(f.options).forEach((o) => { o.selected = [].concat(v).includes(o.value); });
        else if (f.type === "hidden" && form.querySelector(`[data-draft-target="${CSS.escape(f.name)}"]`)) form.querySelector(`[data-draft-target="${CSS.escape(f.name)}"]`).dispatchEvent(new CustomEvent("ui:set", { detail: v }));
        else if (f.type !== "hidden") f.value = v;
        if (f.tagName === "SELECT") f.dispatchEvent(new CustomEvent("ui:refresh"));
        if (f.maxLength > 0) f.dispatchEvent(new Event("input"));
      });
    };
    const time = () => new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" });
    const save = () => {
      if (!key) return;
      try {
        localStorage.setItem(key, JSON.stringify({ at: Date.now(), data: snapshot() }));
        setState("saved", `Draf tersimpan otomatis ${time()}`);
      } catch (e) {
        setState("dirty", "Perubahan belum disimpan");
      }
    };
    const onChange = (e) => {
      if (e && e.target && e.target.closest && e.target.closest("[data-no-draft]")) return;
      dirty = true;
      setState("dirty", key ? "Menyimpan draf..." : "Perubahan belum disimpan");
      if (key) { clearTimeout(timer); timer = setTimeout(save, 700); }
    };
    form.addEventListener("input", onChange);
    form.addEventListener("change", (e) => { if (e.isTrusted || e.target.tagName === "SELECT" || e.target.type === "hidden") onChange(e); });
    form.addEventListener("input", (e) => { if (e.target.matches("input, textarea") && fieldOf(e.target)?.classList.contains("is-invalid") && e.target.checkValidity()) setError(e.target, ""); });
    window.addEventListener("beforeunload", (e) => { if (dirty && !key) { e.preventDefault(); e.returnValue = ""; } });
    if (key) {
      let stored = null;
      try { stored = JSON.parse(localStorage.getItem(key) || "null"); } catch (e) { stored = null; }
      if (stored && stored.data) {
        const when = new Date(stored.at).toLocaleString("id-ID", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
        const yes = el("button", { class: "btn btn--primary btn--sm", type: "button", text: "Pulihkan" });
        const no = el("button", { class: "btn btn--quiet btn--sm", type: "button", text: "Buang" });
        const note = el("div", { class: "notice notice--info", role: "status" }, [
          el("span", { class: "notice__icon", "aria-hidden": "true" }, [icon(ICONS.alert)]),
          el("div", {}, [el("p", { class: "notice__title", text: "Ada draf yang belum dikirim" }), el("p", { class: "notice__text", text: `Terakhir diubah ${when}. Lanjutkan dari situ?` })]),
          el("div", { class: "notice__actions" }, [yes, no])
        ]);
        form.prepend(note);
        yes.addEventListener("click", () => { restore(stored.data); note.remove(); setState("saved", "Draf dipulihkan"); toast("Draf dipulihkan"); });
        no.addEventListener("click", () => { localStorage.removeItem(key); note.remove(); });
      }
    }
    form.addEventListener("submit", (e) => {
      const submitter = e.submitter;
      if (!validate(form)) {
        e.preventDefault();
        toast("Masih ada isian yang perlu diperbaiki.", "danger");
        return;
      }
      dirty = false;
      if (submitter) submitter.classList.add("is-loading");
      form.querySelectorAll("[type=submit]").forEach((b) => { b.setAttribute("aria-disabled", "true"); });
      if (key) localStorage.removeItem(key);
      if (form.hasAttribute("data-demo")) {
        e.preventDefault();
        setTimeout(() => {
          form.querySelectorAll("[type=submit]").forEach((b) => { b.classList.remove("is-loading"); b.removeAttribute("aria-disabled"); });
          const again = submitter && submitter.value === "save_new";
          if (again) {
            const keep = {};
            form.querySelectorAll("[data-keep]").forEach((f) => { keep[f.name] = f.value; });
            form.reset();
            Object.entries(keep).forEach(([name, value]) => { const f = form.elements[name]; if (f) { f.value = value; f.dispatchEvent(new CustomEvent("ui:refresh")); } });
            form.querySelector("input:not([type=hidden]), textarea, [role=combobox]")?.focus();
            toast("Tersimpan. Form siap untuk data berikutnya.");
          } else toast("Data berhasil disimpan.");
          setState("saved", `Tersimpan ${time()}`);
        }, 900);
      }
    });
  };

  const initWizard = (root) => {
    const steps = Array.from(root.querySelectorAll(".wizard__step"));
    const stepper = el("ol", { class: "stepper", "aria-label": "Langkah pengisian" });
    const items = steps.map((step) => el("li", { class: "stepper__item" }, [el("span", { class: "stepper__bar", "aria-hidden": "true" }), el("span", { class: "stepper__label", text: step.dataset.title || "" })]));
    stepper.append(...items);
    const summary = el("p", { class: "stepper__summary", "aria-live": "polite" });
    root.prepend(stepper, summary);
    const back = el("button", { class: "btn btn--secondary", type: "button", text: "Kembali" });
    const next = el("button", { class: "btn btn--primary", type: "button", text: "Lanjut" });
    const submit = root.querySelector("[data-wizard-submit]");
    const nav = el("div", { class: "wizard__nav" }, [back, el("div", { class: "btn-group" }, [next, submit])]);
    root.append(nav);
    let current = 0;
    const buildReview = (step) => {
      const dl = step.querySelector(".review") || step.appendChild(el("dl", { class: "review" }));
      dl.replaceChildren();
      steps.slice(0, -1).forEach((s, index) => {
        const seen = new Set();
        s.querySelectorAll("input, select, textarea").forEach((f) => {
          if (!f.name || seen.has(f.name) || f.type === "hidden" && !f.closest(".datepicker")) return;
          seen.add(f.name);
          let value;
          if (f.type === "file") value = Array.from(f.files).map((x) => x.name).join(", ");
          else if (f.type === "radio" || f.type === "checkbox") value = Array.from(s.querySelectorAll(`[name="${CSS.escape(f.name)}"]:checked`)).map((x) => x.closest("label")?.querySelector(".choice__title, span:last-child")?.textContent || x.value).join(", ");
          else if (f.tagName === "SELECT") value = Array.from(f.selectedOptions).filter((o) => o.value).map((o) => o.text).join(", ");
          else if (f.type === "hidden") value = f.closest(".datepicker").querySelector(".input").value;
          else value = f.value;
          const edit = el("button", { class: "review__edit", type: "button", text: "Ubah", "aria-label": `Ubah ${labelOf(f)}` });
          edit.addEventListener("click", () => go(index, true));
          dl.append(el("div", { class: "review__row" }, [el("dt", { text: labelOf(f) }), el("dd", { text: value || "-" }), edit]));
        });
      });
    };
    const go = (index, focus) => {
      current = index;
      steps.forEach((step, i) => {
        step.hidden = i !== current;
        if (i === current) { step.classList.remove("is-entering"); void step.offsetWidth; step.classList.add("is-entering"); }
      });
      items.forEach((item, i) => {
        item.classList.toggle("is-done", i < current);
        item.classList.toggle("is-current", i === current);
        if (i === current) item.setAttribute("aria-current", "step"); else item.removeAttribute("aria-current");
      });
      summary.textContent = `Langkah ${current + 1} dari ${steps.length}: ${steps[current].dataset.title || ""}`;
      if (steps[current].hasAttribute("data-review")) buildReview(steps[current]);
      back.hidden = current === 0;
      next.hidden = current === steps.length - 1;
      if (submit) submit.hidden = current !== steps.length - 1;
      if (focus) {
        const legend = steps[current].querySelector(".wizard__legend");
        if (legend) { legend.tabIndex = -1; legend.focus({ preventScroll: true }); }
        root.scrollIntoView({ block: "start", behavior: "smooth" });
      }
    };
    next.addEventListener("click", () => { if (validate(steps[current])) go(current + 1, true); });
    back.addEventListener("click", () => go(current - 1, true));
    go(0, false);
  };

  const initShell = () => {
    const sidebar = document.querySelector(".sidebar");
    if (!sidebar) return;
    let scrim = document.querySelector(".scrim");
    if (!scrim) { scrim = el("div", { class: "scrim", "aria-hidden": "true" }); document.body.append(scrim); }
    const toggles = document.querySelectorAll("[data-sidebar-toggle]");
    const desktop = window.matchMedia("(min-width: 1100px)");
    const set = (open) => {
      sidebar.classList.toggle("is-open", open);
      scrim.classList.toggle("is-open", open);
      sidebar.inert = !open && !desktop.matches;
      toggles.forEach((t) => t.setAttribute("aria-expanded", String(open)));
      if (open) sidebar.querySelector("a, button")?.focus();
    };
    desktop.addEventListener("change", () => set(false));
    sidebar.inert = !desktop.matches;
    toggles.forEach((t) => t.addEventListener("click", () => set(!sidebar.classList.contains("is-open"))));
    scrim.addEventListener("click", () => set(false));
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && sidebar.classList.contains("is-open")) { set(false); toggles[0]?.focus(); } });
  };

  const init = (root = document) => {
    root.querySelectorAll("textarea[maxlength], input[maxlength]").forEach(initCounter);
    root.querySelectorAll('select[data-ui="select"], select[data-ui="multiselect"]').forEach(initCombo);
    root.querySelectorAll('input[data-ui="date"]').forEach(initDate);
    root.querySelectorAll('input[type="file"][data-ui="upload"]').forEach(initUpload);
    root.querySelectorAll('form[data-ui="form"]').forEach(initForm);
    root.querySelectorAll('[data-ui="wizard"]').forEach(initWizard);
    root.querySelectorAll("[data-loading-demo]").forEach((btn) => btn.addEventListener("click", () => {
      btn.classList.add("is-loading");
      setTimeout(() => btn.classList.remove("is-loading"), 1500);
    }));
    root.querySelectorAll("[data-toast]").forEach((btn) => btn.addEventListener("click", () => toast(btn.dataset.toast, btn.dataset.toastKind || "success")));
    initShell();
  };

  window.UI = { init, toast, validate };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => init());
  else init();
})();
