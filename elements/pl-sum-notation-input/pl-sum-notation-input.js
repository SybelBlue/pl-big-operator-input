(() => {
  /** Initialize a MathLive field and synchronize its PrairieLearn submission inputs. */
  window.PLSumNotationInput = function (name) {
    const mathField = document.getElementById(`sum-notation-input-${name}`);
    const submissionInput = document.getElementById(`sum-notation-input-sub-${name}`);
    const latexInput = document.getElementById(`sum-notation-input-latex-${name}`);

    if (!mathField || !submissionInput || !latexInput || mathField.dataset.initialized) return;
    mathField.dataset.initialized = 'true';

    if (latexInput.value) mathField.value = latexInput.value;

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
