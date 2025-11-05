import { useState } from 'react'
import { CheckCircle2, XCircle, RotateCcw, ArrowRight } from 'lucide-react'
import { quizQuestions } from '@/data/quizData'

export default function QuizPage() {
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null)
  const [showResult, setShowResult] = useState(false)
  const [score, setScore] = useState(0)
  const [answeredQuestions, setAnsweredQuestions] = useState<number[]>([])

  const question = quizQuestions[currentQuestion]
  const isLastQuestion = currentQuestion === quizQuestions.length - 1
  const isCorrect = selectedAnswer === question.correctAnswer

  const handleAnswerSelect = (answer: string) => {
    if (!showResult) {
      setSelectedAnswer(answer)
    }
  }

  const handleSubmit = () => {
    if (!selectedAnswer) return

    setShowResult(true)
    if (selectedAnswer === question.correctAnswer && !answeredQuestions.includes(currentQuestion)) {
      setScore(score + 1)
      setAnsweredQuestions([...answeredQuestions, currentQuestion])
    }
  }

  const handleNext = () => {
    setSelectedAnswer(null)
    setShowResult(false)
    setCurrentQuestion(currentQuestion + 1)
  }

  const handleReset = () => {
    setCurrentQuestion(0)
    setSelectedAnswer(null)
    setShowResult(false)
    setScore(0)
    setAnsweredQuestions([])
  }

  const getAnswerClass = (answer: string) => {
    if (!showResult) {
      return selectedAnswer === answer
        ? 'border-cloudplus-500 bg-cloudplus-50'
        : 'border-gray-300 hover:border-cloudplus-300'
    }

    if (answer === question.correctAnswer) {
      return 'border-green-500 bg-green-50'
    }

    if (answer === selectedAnswer && answer !== question.correctAnswer) {
      return 'border-red-500 bg-red-50'
    }

    return 'border-gray-300'
  }

  if (isLastQuestion && showResult && selectedAnswer) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="card text-center">
          <div className="mb-6">
            <div className="w-20 h-20 bg-cloudplus-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 className="w-12 h-12 text-white" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Quiz Complete!</h2>
            <p className="text-gray-600">Great job on completing the quiz</p>
          </div>

          <div className="bg-gray-50 rounded-lg p-8 mb-6">
            <div className="text-5xl font-bold text-cloudplus-600 mb-2">
              {score}/{quizQuestions.length}
            </div>
            <div className="text-gray-600">Questions Correct</div>
            <div className="mt-4 text-3xl font-semibold text-gray-900">
              {Math.round((score / quizQuestions.length) * 100)}%
            </div>
          </div>

          <button onClick={handleReset} className="btn-primary inline-flex items-center gap-2">
            <RotateCcw className="w-5 h-5" />
            Restart Quiz
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">
            Question {currentQuestion + 1} of {quizQuestions.length}
          </span>
          <span className="text-sm font-medium text-gray-700">
            Score: {score}/{quizQuestions.length}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-cloudplus-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${((currentQuestion + 1) / quizQuestions.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Question Card */}
      <div className="card">
        <div className="mb-6">
          <span className="inline-block px-3 py-1 bg-cloudplus-100 text-cloudplus-700 rounded-full text-sm font-medium mb-4">
            {question.domain}
          </span>
          <h3 className="text-xl font-bold text-gray-900 mb-4">{question.question}</h3>
        </div>

        {/* Answer Options */}
        <div className="space-y-3 mb-6">
          {question.options.map((option, index) => (
            <button
              key={index}
              onClick={() => handleAnswerSelect(option)}
              disabled={showResult}
              className={`w-full text-left p-4 rounded-lg border-2 transition-all ${getAnswerClass(option)}`}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium">{option}</span>
                {showResult && option === question.correctAnswer && (
                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                )}
                {showResult && option === selectedAnswer && option !== question.correctAnswer && (
                  <XCircle className="w-5 h-5 text-red-600" />
                )}
              </div>
            </button>
          ))}
        </div>

        {/* Explanation */}
        {showResult && (
          <div className={`p-4 rounded-lg mb-6 ${isCorrect ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
            <div className="flex items-start gap-2">
              {isCorrect ? (
                <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5" />
              ) : (
                <XCircle className="w-5 h-5 text-red-600 mt-0.5" />
              )}
              <div>
                <p className={`font-semibold mb-1 ${isCorrect ? 'text-green-900' : 'text-red-900'}`}>
                  {isCorrect ? 'Correct!' : 'Incorrect'}
                </p>
                <p className="text-gray-700 text-sm">{question.explanation}</p>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          {!showResult ? (
            <button
              onClick={handleSubmit}
              disabled={!selectedAnswer}
              className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Submit Answer
            </button>
          ) : (
            <button onClick={handleNext} className="btn-primary flex-1 inline-flex items-center justify-center gap-2">
              {isLastQuestion ? 'Finish Quiz' : 'Next Question'}
              <ArrowRight className="w-5 h-5" />
            </button>
          )}
          <button onClick={handleReset} className="btn-secondary">
            <RotateCcw className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
