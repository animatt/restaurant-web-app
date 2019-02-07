import React, {Component} from 'react';

class Login extends Component {
	constructor(props) {
		super(props);
		this.handleSubmit = this.handleSubmit.bind(this);
	}
	handleSubmit(event) {
		alert('submiting stuff')
		event.preventDefault();
	}
	render() {
		return (
			<div>
			  <h1>Login.</h1>
			  <form onSubmit={this.handleSubmit}>
				<label>
				  Username:
				  <input type="text" name="username" defaultValue="login" />
				</label>
				<br />
				<label>
				  Password:
				  <input type="password" name="password" />
				</label>
			  </form>
			</div>
		);
	}
}
export default Login;
