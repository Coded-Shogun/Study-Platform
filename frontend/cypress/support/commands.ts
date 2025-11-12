/// <reference types="cypress" />

declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Custom command to login as a user
       * @example cy.login('admin', 'Admin123!')
       */
      login(username: string, password: string): Chainable<void>

      /**
       * Custom command to register a new user
       */
      register(userData: {
        username: string
        email: string
        password: string
        fullName: string
        role: string
        studentLevel?: string
      }): Chainable<void>

      /**
       * Custom command to check if authenticated
       */
      checkAuthenticated(): Chainable<boolean>
    }
  }
}

Cypress.Commands.add('login', (username: string, password: string) => {
  cy.visit('/')
  // Implementation will depend on actual login UI
  cy.request({
    method: 'POST',
    url: `${Cypress.env('apiUrl')}/api/auth/login`,
    body: {
      username,
      password,
    },
  }).then((response) => {
    expect(response.status).to.eq(200)
    // Store tokens in localStorage
    window.localStorage.setItem('access_token', response.body.access_token)
    window.localStorage.setItem('refresh_token', response.body.refresh_token)
    window.localStorage.setItem('user', JSON.stringify(response.body.user))
  })
})

Cypress.Commands.add('register', (userData) => {
  cy.request({
    method: 'POST',
    url: `${Cypress.env('apiUrl')}/api/auth/register`,
    body: userData,
  }).then((response) => {
    expect(response.status).to.eq(201)
  })
})

Cypress.Commands.add('checkAuthenticated', () => {
  const token = window.localStorage.getItem('access_token')
  return cy.wrap(!!token)
})

export {}
