(function () {
  // DOM Elements (guarded)
  const form = document.getElementById('preferencesForm');
  if (!form) {
    console.warn('preferencesForm not found — script aborted.');
    return;
  }

  const submitBtn = document.getElementById('submitBtn');
  const btnText = submitBtn ? submitBtn.querySelector('.btn-text') : null;
  const btnLoader = submitBtn ? submitBtn.querySelector('.btn-loader') : null;
  const successMessage = document.getElementById('successMessage');
  const motivationSlider = document.getElementById('motivation');
  const motivationValue = document.getElementById('motivationValue');
  const confidenceLevels = document.getElementById('confidenceLevels');

  // Safe helper to addEventListener if element exists
  function safeOn(el, evt, fn, opts) {
    if (el) el.addEventListener(evt, fn, opts);
  }

  // Update motivation slider value display (if present)
  safeOn(motivationSlider, 'input', function () {
    if (motivationValue) motivationValue.textContent = this.value;
  });

  // Dynamic confidence levels based on selected subjects
  function updateConfidenceLevels() {
    if (!confidenceLevels) return;

    // query current subject inputs so dynamically added subjects are supported
    const currentSubjects = Array.from(document.querySelectorAll('input[name="subjects"]'));
    const selectedSubjects = currentSubjects
      .filter(cb => cb.checked)
      .map(cb => ({
        value: cb.value,
        label: (cb.nextElementSibling && cb.nextElementSibling.textContent) || cb.value
      }));

    if (selectedSubjects.length === 0) {
      confidenceLevels.innerHTML = '<p class="helper-text">Select subjects above to set confidence levels</p>';
      return;
    }

    confidenceLevels.innerHTML = '';
    selectedSubjects.forEach(subject => {
      const confidenceItem = document.createElement('div');
      confidenceItem.className = 'confidence-item';
      confidenceItem.innerHTML = `
            <label>${escapeHtml(subject.label)}</label>
            <div class="confidence-slider">
                <input type="range" 
                       name="confidence_${escapeHtml(subject.value)}" 
                       min="1" 
                       max="5" 
                       value="3" 
                       class="slider"
                       data-subject="${escapeHtml(subject.value)}">
                <span class="confidence-value">3</span>
            </div>
        `;
      confidenceLevels.appendChild(confidenceItem);

      // Add event listener to update confidence value display
      const slider = confidenceItem.querySelector('input[type="range"]');
      const valueDisplay = confidenceItem.querySelector('.confidence-value');
      safeOn(slider, 'input', function () {
        valueDisplay.textContent = this.value;
      });
    });
  }

  // Helper to escape user input for safe insertion into HTML
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // Attach change listeners to any existing static subject checkboxes (if any)
  document.querySelectorAll('input[name="subjects"]').forEach(cb => {
    cb.addEventListener('change', updateConfidenceLevels);
  });

  // --- Added-subjects behavior (ADD button) ---
  const addedSubjectsContainer = document.querySelector('.added-subjects');
  const addSubjectInput = document.getElementById('newSubject');
  const addSubjectBtn = document.getElementById('addSubjectBtn');

  if (addSubjectBtn && addSubjectInput && addedSubjectsContainer) {
    addSubjectBtn.addEventListener('click', function (e) {
      e.preventDefault();

      const raw = addSubjectInput.value?.trim();
      if (!raw) return;

      // Prevent duplicates (case-insensitive)
      const exists = Array.from(document.querySelectorAll('input[name="subjects"]'))
        .some(cb => cb.value.toLowerCase() === raw.toLowerCase());
      if (exists) {
        addSubjectInput.value = '';
        addSubjectInput.focus();
        return;
      }

      // Create label (matching .checkbox-label style)
      const label = document.createElement('label');
      label.className = 'checkbox-label';

      // create checkbox
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.name = 'subjects';
      checkbox.value = raw;
      checkbox.checked = true;

      // create span
      const span = document.createElement('span');
      span.textContent = raw;

      // create remove button
      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'remove-subject';
      removeBtn.title = 'Remove subject';
      removeBtn.textContent = '×';

      // assemble
      label.appendChild(checkbox);
      label.appendChild(span);
      label.appendChild(removeBtn);

      // insert the new subject label before the input field
      // if input is inside addedSubjectsContainer, insert before it; otherwise append
      if (addedSubjectsContainer.contains(addSubjectInput)) {
        addedSubjectsContainer.insertBefore(label, addSubjectInput);
      } else {
        addedSubjectsContainer.appendChild(label);
      }

      // wire events
      checkbox.addEventListener('change', updateConfidenceLevels);
      removeBtn.addEventListener('click', function (ev) {
        ev.preventDefault();
        label.remove();
        updateConfidenceLevels();
      });

      // clear input and update confidence UI
      addSubjectInput.value = '';
      addSubjectInput.focus();
      updateConfidenceLevels();
    });

    // Allow pressing Enter in the newSubject input to add subject
    addSubjectInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        addSubjectBtn.click();
      }
    });
  }

  // Form submission handler
  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    // Show loading state
    if (submitBtn) {
      submitBtn.disabled = true;
      if (btnText) btnText.style.display = 'none';
      if (btnLoader) btnLoader.style.display = 'inline-flex';
    }
    if (successMessage) successMessage.style.display = 'none';

    // Collect form data
    const formData = new FormData(form);
    const data = {
      basicInfo: {
        fullName: formData.get('fullName'),
        educationLevel: formData.get('educationLevel'),
        currentYear: formData.get('currentYear'),
        studyMode: formData.get('studyMode')
      },
      subjectsAndGoals: {
        subjects: formData.getAll('subjects'),
        examGoal: formData.get('examGoal'),
        confidenceLevels: {}
      },
      schedule: {
        studyDays: formData.getAll('studyDays'),
        startTime: formData.get('startTime'),
        endTime: formData.get('endTime'),
        studyDuration: formData.get('studyDuration'),
        breakPreference: formData.get('breakPreference'),
        studyPace: formData.get('studyPace')
      },
      learningStyle: {
        learningStyles: formData.getAll('learningStyle'),
        studyEnvironment: formData.get('studyEnvironment'),
        motivationLevel: formData.get('motivation'),
        focusChallenges: formData.getAll('challenges')
      },
      aiCustomization: {
        aiPlanFocus: formData.get('aiPlanFocus'),
        reminderFrequency: formData.get('reminderFrequency'),
        autoAdjust: formData.get('autoAdjust') === 'on'
      }
    };

    // Collect confidence levels
    const confidenceSliders = document.querySelectorAll('input[type="range"][data-subject]');
    confidenceSliders.forEach(slider => {
      const subject = slider.getAttribute('data-subject');
      data.subjectsAndGoals.confidenceLevels[subject] = parseInt(slider.value);
    });

    // Send preferences to backend
    try {
      const response = await fetch('/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      const result = await response.json();

      // Show success state
      if (btnLoader) btnLoader.style.display = 'none';
      if (btnText) btnText.style.display = 'inline';
      if (submitBtn) submitBtn.disabled = false;

      if (result.success) {
        // Get selected subjects for the quiz
        const subjects = data.subjectsAndGoals.subjects;
        if (subjects && subjects.length > 0) {
          // Redirect to assessment quiz with first subject
          const firstSubject = encodeURIComponent(subjects[0]);
          window.location.href = `/quiz/assessment?subject=${firstSubject}`;
        } else {
          alert('Please select at least one subject');
        }
      } else {
        alert(result.message || 'Failed to save preferences');
        if (successMessage) {
          successMessage.style.display = 'none';
        }
      }
    } catch (error) {
      console.error('Error saving preferences:', error);
      if (btnLoader) btnLoader.style.display = 'none';
      if (btnText) btnText.style.display = 'inline';
      if (submitBtn) submitBtn.disabled = false;
      alert('Error connecting to server');
    }
  });

  // Initialize confidence levels (empty state)
  updateConfidenceLevels();

  // Add smooth scroll behavior
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  // Add active state to radio and checkbox labels
  document.querySelectorAll('.radio-label input, .checkbox-label input').forEach(input => {
    input.addEventListener('change', function () {
      if (this.type === 'radio') {
        const group = this.closest('.radio-group');
        if (group) {
          const siblings = group.querySelectorAll('.radio-label');
          siblings.forEach(label => label.classList.remove('active'));
        }
      }

      const parentLabel = this.closest('label');
      if (this.checked) {
        parentLabel?.classList.add('active');
      } else {
        parentLabel?.classList.remove('active');
      }
    });
  });

  // Add subtle focus effects
  const allInputs = document.querySelectorAll('input, select');
  allInputs.forEach(input => {
    input.addEventListener('focus', function () {
      this.closest('.form-group')?.classList.add('focused');
    });

    input.addEventListener('blur', function () {
      this.closest('.form-group')?.classList.remove('focused');
    });
  });

  console.log('🎓 AI Study Preferences Form loaded successfully!');
})();


document.getElementById("preferencesForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    // Get subjects from added-subjects
    const subjects = Array.from(document.querySelectorAll('.added-subjects input[name="subjects"]')).map(input => input.value);

    const data = {
        fullName: document.getElementById("fullName").value,
        educationLevel: document.getElementById("educationLevel").value,
        currentYear: document.getElementById("currentYear").value,
        subjects: subjects,
        examGoal: document.getElementById("examGoal").value,
        studyDays: Array.from(document.querySelectorAll("input[name='studyDays']:checked")).map(el => el.value),
        startTime: document.getElementById("startTime").value,
        endTime: document.getElementById("endTime").value,
        studyDuration: document.getElementById("studyDuration").value,
        breakPreference: document.getElementById("breakPreference").value,
        aiPlanFocus: document.getElementById("aiPlanFocus").value,
        autoAdjust: document.getElementById("autoAdjust").checked
    };

    document.querySelector(".btn-text").style.display = "none";
    document.querySelector(".btn-loader").style.display = "inline-flex";

    try {
        const response = await fetch("/preferences", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        document.querySelector(".btn-text").style.display = "inline";
        document.querySelector(".btn-loader").style.display = "none";

        if (result.success) {
            // Redirect to assessment quiz with first subject
            if (subjects && subjects.length > 0) {
                const firstSubject = encodeURIComponent(subjects[0]);
                window.location.href = `/quiz/assessment?subject=${firstSubject}`;
            } else {
                alert('Please select at least one subject');
            }
        } else {
            alert(result.message || "Something went wrong");
        }
    } catch (error) {
        console.error(error);
        alert("Error connecting to server");
        document.querySelector(".btn-text").style.display = "inline";
        document.querySelector(".btn-loader").style.display = "none";
    }
});

