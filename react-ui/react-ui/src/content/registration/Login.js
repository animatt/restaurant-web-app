import React, {Component} from 'react';
import cookie from 'react-cookies';
import 'whatwg-fetch';

class Login extends Component {
	constructor(props) {
		super(props);
		this.state = {username: '', passwd: ''}
		this.handleSubmit = this.handleSubmit.bind(this);
		this.handleChange = this.handleChange.bind(this);
	}
	handleChange(event) {
		this.setState({[event.target.name]: event.target.value});
	}
	requestAuthentication() {
		const endpoint = '/accounts/login';
		const csrfToken = cookie.load('csrftoken');
		const lookupOptions = {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'X-CSRFToken': csrfToken
			},
			body: JSON.stringify(this.state),
			credentials: 'include',
		}
		fetch(endpoint, lookupOptions).then(
			response => console.log(response.text())
		);
	}
	handleSubmit(event) {
		this.requestAuthentication();
		event.preventDefault();
	}
	render() {
		return (
			<div>
			  <h1>Login.</h1>
			  <form onSubmit={this.handleSubmit}>
				<label>
				  Username:
				  <input type="text"
						 name="username"
						 defaultValue="username"
						 onChange={this.handleChange}
				  />
				</label>
				<br />
				<label>
				  Password:
				  <input type="password"
						 name="passwd"
						 onChange={this.handleChange}
				  />
				</label>
				<input type="submit" onClick={this.handleSubmit} />
			  </form>
			</div>
		);
	}
}
export default Login;
