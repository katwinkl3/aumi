interface LoadingSpinnerProps {
    message?: string;
  }
  
  const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ message }) => {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>{message || 'Loading...'}</p>
      </div>
    );
  };

const ErrorMessage: React.FC<LoadingSpinnerProps> = ({ message }) => {
    return (
      <div className="error">
        {message || 'An error occurred'}
      </div>
    );
};

export {
    LoadingSpinner,
    ErrorMessage
}