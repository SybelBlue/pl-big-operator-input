(() => {
  /** Initialize a MathLive field and synchronize its PrairieLearn submission inputs. */
  window.PLSumNotationInput = function (name) {
    const mathField = document.getElementById(`sum-notation-input-${name}`);
    const submissionInput = document.getElementById(`sum-notation-input-sub-${name}`);
    const latexInput = document.getElementById(`sum-notation-input-latex-${name}`);

    if (!mathField || !submissionInput || !latexInput || mathField.dataset.initialized) return;
    mathField.dataset.initialized = 'true';

    if (latexInput.value) mathField.value = latexInput.value;

    // Keep this layout in sync with PrairieLearn's pl-symbolic-input math keyboard.
    const keyboardLayout = {
      label: 'math',
      rows: [
        [
          { class: 'small', latex: '{#@}^{#?}' },
          {
            class: 'small',
            latex: '{#@}^{2}',
            variants: [{ class: 'small', latex: '{#@}^{3}' }],
          },
          {
            class: 'small',
            latex: '\\frac{#@}{#?}',
            width: 1.3,
            variants: [{ class: 'small', latex: '\\frac{1}{#@}' }],
          },
          '[separator]',
          '7',
          '8',
          '9',
          '+',
          '[separator]',
          'e',
          '\\infty',
          '\\pi',
        ],
        [
          { class: 'small', latex: '\\sqrt', insert: '\\sqrt{#0}' },
          {
            class: 'small',
            latex: '\\log',
            insert: '\\operatorname{log}\\left({#0}\\right)',
          },
          { class: 'small', latex: '!' },
          '[separator]',
          '4',
          '5',
          '6',
          '-',
          '[separator]',
          'x',
          'y',
          'i',
        ],
        [
          { class: 'small', latex: '|#0|', insert: '|{#0}|' },
          {
            class: 'small',
            latex: '\\min',
            insert: '\\operatorname{min}\\left({#0}\\right)',
          },
          {
            class: 'small',
            latex: '\\max',
            insert: '\\operatorname{max}\\left({#0}\\right)',
          },
          '[separator]',
          '1',
          '2',
          '3',
          '\\times',
          '[separator]',
          '(',
          ')',
          {
            class: 'small',
            latex: '\\mathrm{sign}',
            insert: '\\operatorname{sign}\\left({#0}\\right)',
          },
        ],
        [
          {
            class: 'small',
            latex: '\\sin',
            insert: '\\operatorname{sin}\\left({#0}\\right)',
          },
          {
            class: 'small',
            latex: '\\cos',
            insert: '\\operatorname{cos}\\left({#0}\\right)',
          },
          {
            class: 'small',
            latex: '\\tan',
            insert: '\\operatorname{tan}\\left({#0}\\right)',
          },
          '[separator]',
          { latex: '0', width: 2 },
          '.',
          '/',
          '[separator]',
          { class: 'small hide-shift', label: '[left]' },
          { class: 'small hide-shift', label: '[right]' },
          { class: 'small hide-shift', label: '[backspace]', shift: null, width: 1 },
        ],
      ],
    };

    const updateKeyboardLayout = () => {
      window.mathVirtualKeyboard.layouts = [keyboardLayout, 'alphabetic', 'greek'];
    };

    mathField.addEventListener('focus', updateKeyboardLayout);
    mathField.addEventListener('selection-change', updateKeyboardLayout);

    mathField.popoverPolicy = 'off';
    mathField.setAttribute('placeholder', `\\text{${mathField.dataset.placeholderText ?? ''}}`);

    const updateSubmissionData = () => {
      submissionInput.value = mathField.getValue('plain-text');
      latexInput.value = mathField.getValue('latex');
    };

    updateSubmissionData();
    mathField.addEventListener('input', updateSubmissionData);
    mathField.addEventListener(
      'keydown',
      (event) => {
        if (event.key === '\\') {
          event.preventDefault();
          mathField.executeCommand(['insert', '\\backslash']);
        } else if (event.key === 'Escape') {
          event.preventDefault();
        }
      },
      { capture: true },
    );
  };
})();
