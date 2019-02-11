import React, { Component } from 'react';
import {BrowserRouter as Router, Route} from 'react-router-dom';
import 'whatwg-fetch';

import './App.css';

import Navbar from './navbar/Navbar';
import Content from './content/Content';

class App extends Component {
	constructor(props) {
		super(props);
		this.state = {loggedIn: false, userName: ''};
	}
	componentDidMount() {
		const endpoint = '/accounts/credentials';
		const lookupOptions = {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
			}
		}
		fetch(endpoint, lookupOptions).then(
			response => this.setState(response.json())
		);
	}
	setLogin(loggedIn, username) {
		this.setState({loggedIn, username}); 
	}
	render() {
		return (
			<Router>
			  <div className="App">
				<Navbar loggedIn={this.state.loggedIn}
						userName={this.state.username} />
				<Content setLogin={this.setLogin} />
			  </div>
			</Router>
		);
	}
}

export default App;
