import React, { Component } from 'react';
import {BrowserRouter as Router, Route} from 'react-router-dom';
import 'whatwg-fetch';
import cookie from 'react-cookies';

import './App.css';

import Navbar from './navbar/Navbar';
import Content from './content/Content';

class App extends Component {
	constructor(props) {
		super(props);
		this.state = {loggedIn: false, userName: ''};
	}
	componentDidMount() {
		const endpoint = '/accounts';
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
	render() {
		return (
			<Router>
			  <div className="App">
				<Navbar loggedIn={this.loggedIn} userName={this.username} />
				<Content />
			  </div>
			</Router>
		);
	}
}

export default App;
