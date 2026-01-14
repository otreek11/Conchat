import { useState } from 'react';
import './Login.css';

// ==================== CONFIGURAÇÃO DA API ====================

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// ==================== INTERFACES E TIPOS ====================

interface LoginFormData {
  username: string;
  password: string;
}

interface LoginFormErrors {
  username?: string;
  password?: string;
  general?: string;
}

interface LoginApiSuccessResponse {
  message: string;
  access_token: string;
  refresh_token: string;
}

interface LoginApiErrorResponse {
  message: string;
}

// ==================== COMPONENTE PRINCIPAL ====================

function Login() {
  // ==================== ESTADOS ====================

  const [formData, setFormData] = useState<LoginFormData>({
    username: '',
    password: '',
  });

  const [errors, setErrors] = useState<LoginFormErrors>({});
  const [touched, setTouched] = useState<Set<keyof LoginFormData>>(new Set());
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showSuccess, setShowSuccess] = useState<boolean>(false);

  // ==================== FUNÇÕES DE VALIDAÇÃO ====================

  const validateUsername = (username: string): string | undefined => {
    if (!username.trim()) {
      return 'Username é obrigatório';
    }
    return undefined;
  };

  const validatePassword = (password: string): string | undefined => {
    if (!password.trim()) {
      return 'Senha é obrigatória';
    }
    return undefined;
  };

  const validateField = (field: keyof LoginFormData, value: string): boolean => {
    let error: string | undefined;

    switch (field) {
      case 'username':
        error = validateUsername(value);
        break;
      case 'password':
        error = validatePassword(value);
        break;
    }

    setErrors((prev) => ({ ...prev, [field]: error }));
    return !error;
  };

  const validateAllFields = (): boolean => {
    const newErrors: LoginFormErrors = {};

    newErrors.username = validateUsername(formData.username);
    newErrors.password = validatePassword(formData.password);

    setErrors(newErrors);

    return !Object.values(newErrors).some((error) => error !== undefined);
  };

  // ==================== HANDLERS ====================

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // Se o campo já foi tocado, valida em tempo real
    if (touched.has(name as keyof LoginFormData)) {
      validateField(name as keyof LoginFormData, value);
    }
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setTouched((prev) => new Set(prev).add(name as keyof LoginFormData));
    validateField(name as keyof LoginFormData, value);
  };

  // ==================== INTEGRAÇÃO BACKEND ====================

  const handleApiError = (status: number, data: LoginApiErrorResponse) => {
    switch (status) {
      case 400:
        // Parâmetros ausentes
        setErrors((prev) => ({
          ...prev,
          general: data.message || 'Campos obrigatórios faltando.',
        }));
        break;

      case 404:
        // Credenciais inválidas
        // Backend retorna: "User not found or wrong password"
        setErrors((prev) => ({
          ...prev,
          general: 'Username ou senha incorretos.',
        }));
        break;

      case 500:
        // Erro interno do servidor
        setErrors((prev) => ({
          ...prev,
          general: 'Erro no servidor. Tente novamente mais tarde.',
        }));
        break;

      default:
        setErrors((prev) => ({
          ...prev,
          general: data.message || 'Erro desconhecido. Tente novamente.',
        }));
    }
  };

  const handleApiSuccess = (data: LoginApiSuccessResponse) => {
    // Salvar tokens no localStorage
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);

    // Mostrar mensagem de sucesso
    setShowSuccess(true);

    // Limpar formulário
    setFormData({
      username: '',
      password: '',
    });
    setTouched(new Set());
    setErrors({});

    // Log para debug (roteamento será implementado futuramente)
    console.log('Login bem-sucedido!');
    console.log('Tokens salvos no localStorage');
  };

  const submitLogin = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: formData.username.trim(),
          password: formData.password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        handleApiError(response.status, data);
        return;
      }

      handleApiSuccess(data);
    } catch (error) {
      console.error('Erro na requisição:', error);
      setErrors((prev) => ({
        ...prev,
        general: 'Erro ao conectar com o servidor. Tente novamente.',
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Marcar todos os campos como tocados
    setTouched(new Set<keyof LoginFormData>(['username', 'password']));

    // Validar todos os campos
    const isValid = validateAllFields();
    if (!isValid) return;

    setIsLoading(true);
    setErrors((prev) => ({ ...prev, general: undefined }));

    try {
      await submitLogin();
    } finally {
      setIsLoading(false);
    }
  };

  // ==================== RENDER ====================

  return (
    <div className="login-container">
      <div className="login-card">
        <header className="login-header">
          <h1>Entrar</h1>
          <p>Acesse sua conta no Conchat</p>
        </header>

        {showSuccess && (
          <div className="success-message" role="alert">
            <p>Login realizado com sucesso!</p>
          </div>
        )}

        {errors.general && (
          <div className="error-message-general" role="alert">
            <p>{errors.general}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form" noValidate>
          {/* Campo Username */}
          <div className="form-group">
            <label htmlFor="username" className="form-label">
              Username <span className="required">*</span>
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              onBlur={handleBlur}
              className={`form-input ${errors.username && touched.has('username') ? 'input-error' : ''}`}
              placeholder="seu_username"
              aria-invalid={!!errors.username && touched.has('username')}
              aria-describedby={errors.username ? 'username-error' : undefined}
              disabled={isLoading}
            />
            {errors.username && touched.has('username') && (
              <span id="username-error" className="error-message" role="alert">
                {errors.username}
              </span>
            )}
          </div>

          {/* Campo Password */}
          <div className="form-group">
            <label htmlFor="password" className="form-label">
              Senha <span className="required">*</span>
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              onBlur={handleBlur}
              className={`form-input ${errors.password && touched.has('password') ? 'input-error' : ''}`}
              placeholder="••••••••"
              aria-invalid={!!errors.password && touched.has('password')}
              aria-describedby={errors.password ? 'password-error' : undefined}
              disabled={isLoading}
            />
            {errors.password && touched.has('password') && (
              <span id="password-error" className="error-message" role="alert">
                {errors.password}
              </span>
            )}
          </div>

          {/* Botão de Submit */}
          <button type="submit" className="submit-btn" disabled={isLoading} aria-busy={isLoading}>
            {isLoading ? (
              <>
                <span className="spinner" aria-hidden="true"></span>
                Entrando...
              </>
            ) : (
              'Entrar'
            )}
          </button>
        </form>

        <footer className="login-footer">
          <p>
            Não tem uma conta? <a href="#cadastro">Cadastre-se</a>
          </p>
        </footer>
      </div>
    </div>
  );
}

export default Login;
