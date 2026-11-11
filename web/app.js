(function () {
  "use strict";

  const CHOICE_LETTERS = ["A", "B", "C", "D"];

  const quizScreen = document.getElementById("quiz-screen");
  const endScreen = document.getElementById("end-screen");
  const loadingScreen = document.getElementById("loading-screen");
  const questionIdEl = document.getElementById("question-id");
  const questionTextEl = document.getElementById("question-text");
  const choicesEl = document.getElementById("choices");
  const feedbackEl = document.getElementById("feedback");
  const nextBtn = document.getElementById("next-btn");
  const quitBtn = document.getElementById("quit-btn");
  const restartBtn = document.getElementById("restart-btn");
  const scoreDisplay = document.getElementById("score-display");
  const finalScoreEl = document.getElementById("final-score");

  // Deck: hands out questions in random order without repeats until the
  // whole bank has been asked once, then reshuffles and starts over.
  let order = [];
  let correctCount = 0;
  let totalCount = 0;
  let currentQuestion = null;
  let currentMapping = null; // display letter -> original bank letter

  function shuffle(array) {
    for (let i = array.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
  }

  function drawQuestion() {
    if (order.length === 0) {
      order = shuffle(QUESTIONS.map((_, i) => i));
    }
    return QUESTIONS[order.pop()];
  }

  function updateScoreDisplay() {
    scoreDisplay.textContent = `Score: ${correctCount}/${totalCount}`;
  }

  function showQuestion() {
    currentQuestion = drawQuestion();
    totalCount += 1;
    updateScoreDisplay();

    questionIdEl.textContent = `[${currentQuestion.id}]`;
    questionTextEl.textContent = currentQuestion.question;

    const shuffledLetters = shuffle(CHOICE_LETTERS.slice());
    currentMapping = {};
    choicesEl.innerHTML = "";

    CHOICE_LETTERS.forEach((displayLetter, i) => {
      const originalLetter = shuffledLetters[i];
      currentMapping[displayLetter] = originalLetter;

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "choice-btn";
      btn.dataset.letter = displayLetter;

      const letterSpan = document.createElement("span");
      letterSpan.className = "letter";
      letterSpan.textContent = `${displayLetter})`;

      const textSpan = document.createElement("span");
      textSpan.textContent = currentQuestion.choices[originalLetter];

      btn.append(letterSpan, textSpan);
      btn.addEventListener("click", () => handleAnswer(displayLetter));
      choicesEl.appendChild(btn);
    });

    feedbackEl.textContent = "";
    feedbackEl.className = "feedback";
    nextBtn.hidden = true;
  }

  function handleAnswer(displayLetter) {
    const chosenOriginal = currentMapping[displayLetter];
    const isCorrect = chosenOriginal === currentQuestion.answer;
    const correctDisplayLetter = Object.keys(currentMapping).find(
      (d) => currentMapping[d] === currentQuestion.answer
    );

    Array.from(choicesEl.children).forEach((btn) => {
      btn.disabled = true;
      if (btn.dataset.letter === correctDisplayLetter) {
        btn.classList.add("correct");
      } else if (btn.dataset.letter === displayLetter && !isCorrect) {
        btn.classList.add("incorrect");
      }
    });

    if (isCorrect) {
      correctCount += 1;
      feedbackEl.textContent = "Correct!";
      feedbackEl.className = "feedback correct";
    } else {
      feedbackEl.textContent =
        `Incorrect. The correct answer was ${correctDisplayLetter}) ` +
        currentQuestion.choices[currentQuestion.answer];
      feedbackEl.className = "feedback incorrect";
    }

    updateScoreDisplay();
    nextBtn.hidden = false;
    nextBtn.focus();
  }

  function showEndScreen() {
    quizScreen.hidden = true;
    endScreen.hidden = false;
    const pct = totalCount === 0 ? 0 : (100 * correctCount) / totalCount;
    finalScoreEl.textContent =
      totalCount === 0
        ? "No questions answered."
        : `${correctCount}/${totalCount} correct (${pct.toFixed(1)}%)`;
  }

  function restart() {
    order = [];
    correctCount = 0;
    totalCount = 0;
    endScreen.hidden = true;
    quizScreen.hidden = false;
    showQuestion();
  }

  nextBtn.addEventListener("click", showQuestion);
  quitBtn.addEventListener("click", showEndScreen);
  restartBtn.addEventListener("click", restart);

  // Mirror the CLI's keyboard-driven flow: A/B/C/D answers, Q quits.
  document.addEventListener("keydown", (e) => {
    if (quizScreen.hidden) return;
    const key = e.key.toUpperCase();
    if (CHOICE_LETTERS.includes(key) && nextBtn.hidden) {
      const btn = choicesEl.querySelector(`[data-letter="${key}"]`);
      if (btn && !btn.disabled) btn.click();
    } else if (key === "ENTER" && !nextBtn.hidden) {
      nextBtn.click();
    } else if (key === "Q") {
      showEndScreen();
    }
  });

  if (typeof QUESTIONS === "undefined" || QUESTIONS.length === 0) {
    loadingScreen.querySelector("p").textContent =
      "Error: could not load questions.js (run extract_questions.py first).";
  } else {
    loadingScreen.hidden = true;
    quizScreen.hidden = false;
    showQuestion();
  }
})();
