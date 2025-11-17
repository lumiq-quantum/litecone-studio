import { useState, useEffect } from 'react';

const TUTORIAL_STORAGE_KEY = 'workflow-ui-tutorial-completed';

export function useTutorial() {
  const [showTutorial, setShowTutorial] = useState(false);
  const [tutorialCompleted, setTutorialCompleted] = useState(false);

  useEffect(() => {
    // Check if tutorial has been completed
    const completed = localStorage.getItem(TUTORIAL_STORAGE_KEY) === 'true';
    setTutorialCompleted(completed);
  }, []);

  const startTutorial = () => {
    setShowTutorial(true);
  };

  const completeTutorial = () => {
    localStorage.setItem(TUTORIAL_STORAGE_KEY, 'true');
    setTutorialCompleted(true);
    setShowTutorial(false);
  };

  const skipTutorial = () => {
    localStorage.setItem(TUTORIAL_STORAGE_KEY, 'true');
    setTutorialCompleted(true);
    setShowTutorial(false);
  };

  const resetTutorial = () => {
    localStorage.removeItem(TUTORIAL_STORAGE_KEY);
    setTutorialCompleted(false);
  };

  return {
    showTutorial,
    tutorialCompleted,
    startTutorial,
    completeTutorial,
    skipTutorial,
    resetTutorial,
  };
}
