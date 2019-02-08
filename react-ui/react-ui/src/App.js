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
		this.state = {loggedIn: false};
	}
	componentDidMount() {
		// fetch browser session
		this.setState({});
	}
	render() {
		return (
			<Router>
			  <div className="App">
				<Navbar />
				<Content />
			  </div>
			</Router>
		);
	}
}

export default App;
